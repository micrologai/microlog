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

from microlog.config import micrologBackgroundService

class StatusGenerator(threading.Thread):
    def __init__(self):
        import psutil
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.lastCpuSample = time.time()
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
        cpuTimes = psutil.Process().cpu_times()
        now = time.time()
        duration = now - self.lastCpuSample
        user = cpuTimes.user - self.lastCpuTimes.user
        system = cpuTimes.system - self.lastCpuTimes.system
        cpu = min(100, (user + system) * 100 / duration)
        self.lastCpuTimes = cpuTimes
        self.lastCpuSample = now
        return Process(cpu)
    
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
    def __init__(self, cpu):
        self.cpu = cpu

    def __eq__(self, other):
        return other and self.cpu == other.cpu


class Status():
    def __init__(self, when, system: System, process: Process, python: Python):
        self.when = when
        self.system = system
        self.process = process
        self.python = python
        self.duration = 0

    @classmethod
    def load(cls, event: list):
        # typical event: [2, 0.058, [0.0, 34359738368, 31186944], [85777, 1, 0.0, 0.03, 20, 4, 4], [334]]
        _, when, system, process, python = event
        return Status(when, System(*system), Process(*process), Python(*python))

    def save(self):
        events.put([
            config.EVENT_KIND_STATUS,
            self.when,
            [
                self.system.cpu,
                self.system.memoryTotal,
                self.system.memoryFree,
            ],
            [
                self.process.cpu,
            ],
            [
                self.python.moduleCount,
            ],
        ])

    def __eq__(self, other):
        return other and self.system == other.system and self.process == other.process and self.python == other.python


