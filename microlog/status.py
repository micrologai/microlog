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


class StatusGenerator(threading.Thread):
    def __init__(self):
        import psutil
        threading.Thread.__init__(self)
        self.daemon = True
        self.lastCpuSampleTime = events.now()
        self.lastCpuTimes = psutil.Process().cpu_times()
        self.cpu = 0
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

    def getProcess(self) -> Process:
        import psutil
        process = psutil.Process()
        cpuTimes = process.cpu_times()
        now = events.now()
        duration = now - self.lastCpuSampleTime
        user = cpuTimes.user - self.lastCpuTimes.user
        system = cpuTimes.system - self.lastCpuTimes.system
        cpu = min(100, (user + system) * 100 / duration)
        self.lastCpuTimes = cpuTimes
        self.lastCpuSampleTime = now
        memory = process.memory_info().rss
        return Process(cpu, memory)
    
    @micrologBackgroundService("Status")
    def sample(self) -> None:
        Status(events.now(), self.getSystem(), self.getProcess(), self.getPython()).save()

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
    def load(cls, event: list):
        _, whenIndex, system, process, python = event
        systemCpu, systemMemoryTotalIndex, systemMemoryFreeIndex = system
        cpu, memory = process
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
            ],
            [
                self.python.moduleCount,
            ],
        ])

    def __eq__(self, other):
        return other and self.system == other.system and self.process == other.process and self.python == other.python


