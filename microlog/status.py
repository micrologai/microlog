#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import sys
import threading
import time


from microlog import config
from microlog import events
from microlog import settings
from microlog import symbols

from microlog.config import micrologBackgroundService

KB = 1024
MB = KB * KB
GB = MB * KB


class StatusGenerator(threading.Thread):
    memoryWarning = 0

    def __init__(self):
        import psutil
        threading.Thread.__init__(self)
        self.daemon = True
        self.lastCpuSample = (events.now(), psutil.Process().cpu_times())
        self.startProcess = self.getProcess()
        self.sample()

    def run(self) -> None:
        while True:
            self.sample()
            time.sleep(settings.current.statusDelay)

    def getSystem(self: float) -> System:
        import psutil
        memory = psutil.virtual_memory()
        return System(
            psutil.cpu_percent() / psutil.cpu_count(),
            memory.total,
            memory.free,
        )

    def getProcess(self, startProcess: Process=None) -> Process:
        import psutil
        process = psutil.Process()
        now = events.now()

        networkIO = psutil.net_io_counters()
        diskIO = psutil.disk_io_counters()
        with process.oneshot():
            memory = process.memory_info()
            cpuTimes = process.cpu_times()

        def getCpu():
            lastCpuSampleTime, lastCpuTimes = self.lastCpuSample
            user = cpuTimes.user - lastCpuTimes.user
            system = cpuTimes.system - lastCpuTimes.system
            duration = now - lastCpuSampleTime
            cpu = min(100, (user + system) * 100 / duration)
            self.lastCpuSample = (now, cpuTimes)
            return cpu

        def getMemory():
            self.checkMemory(memory.rss)
            return memory.rss

        def getDiskIO():
            return (
                diskIO.read_bytes - (startProcess.diskRead if startProcess else 0),
                diskIO.write_bytes - (startProcess.diskWrite if startProcess else 0),
            )

        def getNetworkIO():
            return (
                networkIO.bytes_recv - (startProcess.networkRead if startProcess else 0),
                networkIO.bytes_sent - (startProcess.networkWrite if startProcess else 0),
            )

        return Process(
            getCpu(),
            getMemory(),
            *getDiskIO(),
            *getNetworkIO(),
        )


    def checkMemory(self, memory):
        gb = int(memory / GB)
        if gb > StatusGenerator.memoryWarning:
            from microlog import warn
            StatusGenerator.memoryWarning = gb
            warn(f"<b style='color: red'>WARNING</b><br> Python process memory grew to {memory / GB:.1f} GB")
    
    @micrologBackgroundService("Status")
    def sample(self) -> None:
        Status(events.now(), self.getSystem(), self.getProcess(self.startProcess), self.getPython()).save()

    def getPython(self) -> Python:
        return Python(len(sys.modules))

    def stop(self):
        self.sample()
        self.sample()


class System():
    def __init__(self, cpu, memoryTotal, memoryFree):
        self.cpu = cpu
        self.memoryTotal = memoryTotal
        self.memoryFree = memoryFree

    def __eq__(self, other):
        return other and self.cpu == other.cpu and self.memoryFree == other.memoryFree and self.memoryTotal == other.memoryTotal

class Python():
    def __init__(self, moduleCount):
        self.moduleCount = moduleCount

    def __eq__(self, other):
        return other and self.moduleCount == other.moduleCount


class Process():
    def __init__(self, cpu, memory, diskRead, diskWrite, networkRead, networkWrite):
        self.cpu = cpu
        self.memory = memory
        self.diskRead = diskRead
        self.diskWrite = diskWrite
        self.networkRead = networkRead
        self.networkWrite = networkWrite

    def __eq__(self, other):
        return other and self.cpu == other.cpu and self.memory == other.memory  and \
                self.diskRead == other.diskRead and self.diskWrite == other.diskWrite and \
                self.networkRead == other.networkRead and self.networkWrite == other.networkWrite


class Status():
    def __init__(self, when, system: System, process: Process, python: Python):
        self.when = when
        self.system = system
        self.process = process
        self.python = python
        self.duration = 0

    @classmethod
    def load(cls, event: list):
        print("load", event)
        _, whenIndex, system, process, python = event
        systemCpu, systemMemoryTotalIndex, systemMemoryFreeIndex = system
        cpu, memory, diskRead, diskWrite, networkRead, networkWrite = process
        moduleCount = python[0]
        return Status(
            symbols.get(whenIndex),
            System(
                systemCpu,
                symbols.get(systemMemoryTotalIndex),
                symbols.get(systemMemoryFreeIndex),
            ),
            Process(
                cpu,
                memory,
                diskRead,
                diskWrite,
                networkRead,
                networkWrite,
            ),
            Python(
                moduleCount,
            )
        )

    def save(self):
        events.put([
            config.EVENT_KIND_STATUS,
            symbols.index(round(self.when, 3)),
            [
                round(self.system.cpu, 2),
                symbols.index(self.system.memoryTotal),
                symbols.index(self.system.memoryFree),
            ],
            [
                round(self.process.cpu, 2),
                self.process.memory,
                self.process.diskRead,
                self.process.diskWrite,
                self.process.networkRead,
                self.process.networkWrite,
            ],
            [
                self.python.moduleCount,
            ],
        ])

    def __eq__(self, other):
        return other and self.system == other.system and self.process == other.process and self.python == other.python


