#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import json
import sys

from microlog import config
from microlog import events
from microlog import meta
from microlog import settings
from microlog import threads
from microlog import symbols
from microlog import memory


KB = 1024
MB = KB * KB
GB = MB * KB


class StatusGenerator(threads.BackgroundThread):
    memoryWarning = 0

    def start(self):
        import psutil
        self.daemon = True
        self.lastCpuSample = (events.now(), psutil.Process().cpu_times())
        self.startProcess = self.getProcess()
        self.delay = settings.current.statusDelay
        self.tick()
        self.saveMeta()
        return threads.BackgroundThread.start(self)

    def saveMeta(self):
        main = sys.argv[0].replace(".py", "").replace("/", ".")
        meta.Meta(config.EVENT_KIND_META, events.now(), main).marshall()

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

        return Process(
            getCpu(),
            getMemory(),
        )


    def checkMemory(self, memory):
        gb = int(memory / GB)
        if gb > StatusGenerator.memoryWarning:
            from microlog import warn
            StatusGenerator.memoryWarning = gb
            warn(f"<b style='color: red'>WARNING</b><br> Python process memory grew to {memory / GB:.1f} GB")
    
    def tick(self) -> None:
        Status(events.now(), self.getSystem(), self.getProcess(self.startProcess), self.getPython()).marshall()

    def getPython(self) -> Python:
        return Python(len(sys.modules))

    def stop(self):
        self.tick()
        self.tick()


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
    def __init__(self, cpu, memory):
        self.cpu = cpu
        self.memory = memory

    def __eq__(self, other):
        return other and self.cpu == other.cpu and self.memory == other.memory 


class Status():
    def __init__(self, when, system: System, process: Process, python: Python):
        self.when = when
        self.system = system
        self.process = process
        self.python = python
        self.duration = 0

    @classmethod
    def unmarshall(cls, event: list):
        _, whenIndex, dataIndex = event
        system, process, python = json.loads(symbols.get(dataIndex))
        systemCpu, systemMemoryTotal, systemMemoryFree= system
        cpu, memory = process
        moduleCount = python[0]
        return Status(
            symbols.get(whenIndex),
            System(
                systemCpu,
                systemMemoryTotal,
                systemMemoryFree,
            ),
            Process(
                cpu,
                memory,
            ),
            Python(
                moduleCount,
            )
        )

    def marshall(self):
        events.put([
            config.EVENT_KIND_STATUS,
            symbols.index(round(self.when, 3)),
            symbols.index(json.dumps([
                [
                    round(self.system.cpu),
                    round(self.system.memoryTotal / memory.GB, 1),
                    round(self.system.memoryFree / memory.GB, 1),
                ],
                [
                    round(self.process.cpu),
                    round(self.process.memory / memory.GB, 1),
                ],
                [
                    self.python.moduleCount,
                ]
            ])),
        ])

    def __eq__(self, other):
        return other and self.system == other.system and self.process == other.process and self.python == other.python


