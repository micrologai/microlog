#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import os
import sys
import traceback


KB = 1024
MB = KB * KB
GB = MB * KB


class Call():
    def __init__(self, when: float, threadId: int, callSite: CallSite, callerSite: CallSite, depth: int, duration: float = 0.0):
        self.when = when
        assert isinstance(threadId, int), "threadId should be a number"
        self.threadId = threadId
        assert isinstance(callSite, CallSite), f"callSite should be a CallSite, not {type(callSite)}: {callSite}"
        self.callSite = callSite
        self.callerSite = callerSite
        self.depth = depth
        self.duration = duration

    @classmethod
    def fromDict(self, values):
        return Call(
            values["when"],
            values["threadId"],
            CallSite.fromDict(values["callSite"]),
            CallSite.fromDict(values["callerSite"]),
            values["depth"],
            values["duration"],
        )

    def isSimilar(self, other: Call):
        return other and self.callSite.isSimilar(other.callSite) and self.callerSite.isSimilar(other.callerSite)

    def __eq__(self, other: Call):
        return other and self.callSite == other.callSite and self.callerSite == other.callerSite

    def __hash__(self):
        return hash((self.callSite, self.callerSite))

    def __repr__(self):
        return f"<Call {self.callSite.name}@{self.callSite.lineno}>"

def memoize(function):
    memo = {}
    def helper(x):
        if x not in memo:            
            memo[x] = function(x)
        return memo[x]
    return helper

def absolutePath(filename):
    return os.path.abspath(filename)

class CallSite():
    def __init__(self, filename, lineno, name):
        self.filename = absolutePath(filename)
        self.lineno = lineno or 0
        self.name = name

    @classmethod
    def fromDict(self, values):
        return CallSite(
            values["filename"] if values else "",
            values["lineno"] if values else "",
            values["name"] if values else "..",
        )

    def isSimilar(self, other: CallSite):
        return other and self.filename == other.filename and self.lineno == other.lineno and self.name == other.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return f"<CallSite {self.filename}:{self.name}:{self.lineno}>"


class Stack():
    def __init__(self, when=0, threadId=0, startFrame=None) -> None:
        from microlog import log
        self.when = when or log.log.now()
        self.calls = []
        if startFrame:
            callerSite = None
            for depth, frameLineno in enumerate(self.walkStack(startFrame)):
                frame, lineno = frameLineno
                callSite = self.callSiteFromFrame(frame, lineno)
                if not callSite:
                    break
                self.calls.append(Call(when, threadId, callSite, callerSite, depth, 0))
                callerSite = callSite
            
    def walkStack(self, startFrame):
        stack = [
            (frame, lineno)
            for frame, lineno in reversed(list(traceback.walk_stack(startFrame)))
        ]
        return stack
            
    def callSiteFromFrame(self, frame, lineno):
        filename = frame.f_globals.get("__file__", "")
        module = frame.f_globals.get("__name__", "")
        if module == "__main__":
            module = sys.argv[0].replace(".py", "").replace("/", ".")
        instance = frame.f_locals["self"] if "self" in frame.f_locals else None
        clazz = ""
        if instance is not None:
            clazz = instance.__class__.__name__
            module = instance.__module__
        name = frame.f_code.co_name
        if self.ignore(module):
            return None
        return CallSite(filename, lineno, f"{module}.{clazz}.{name}")
        
    def ignore(self, module):
        from microlog import config
        return module in config.IGNORE_MODULES or module.startswith("importlib.")

    def __iter__(self):
        return iter(self.calls)

    def __len__(self):
        return len(self.calls)
    
    def __getitem__(self, index):
         return self.calls[index]

    def __repr__(self):
        calls = "\n  ".join(map(str, self.calls))
        return f"<Stack\n  {calls}\n>"


class Marker():
    def __init__(self, kind: int, when:float, message: str, stack:List[str]):
        self.when = when
        self.kind = kind
        self.message = message
        self.stack = stack
        self.duration = 0.1

    @classmethod
    def fromDict(self, values):
        return Marker(
            values["kind"],
            values["when"],
            values["message"],
            values["stack"],
        )


class System():
    def __init__(self, cpu, memoryTotal, memoryFree):
        self.cpu = cpu
        self.memoryTotal = memoryTotal
        self.memoryFree = memoryFree

    @classmethod
    def fromDict(self, values):
        return System(
            values["cpu"],
            values["memoryTotal"],
            values["memoryFree"],
        )

    def __eq__(self, other):
        return other and self.cpu == other.cpu and self.memoryFree == other.memoryFree and self.memoryTotal == other.memoryTotal

class Python():
    def __init__(self, moduleCount):
        self.moduleCount = moduleCount

    @classmethod
    def fromDict(self, values):
        return Python(
            values["moduleCount"],
        )

    def __eq__(self, other):
        return other and self.moduleCount == other.moduleCount


class Process():
    def __init__(self, cpu, memory):
        self.cpu = cpu
        self.memory = memory

    @classmethod
    def fromDict(self, values):
        return Process(
            values["cpu"],
            values["memory"],
        )

    def __eq__(self, other):
        return other and self.cpu == other.cpu and self.memory == other.memory 


class Status():
    def __init__(self, when, system: System, process: Process, python: Python):
        assert isinstance(when, float), f"when should be a float, not {type(when)}: {when}"
        self.when = when
        self.system = system
        self.process = process
        self.python = python
        self.duration = 0

    @classmethod
    def fromDict(self, values):
        return Status(
            values["when"],
            System.fromDict(values["system"]),
            Process.fromDict(values["process"]),
            Python.fromDict(values["python"]),
        )

    def __eq__(self, other):
        return other and self.system == other.system and self.process == other.process and self.python == other.python


def toGB(amount):
    if amount / GB > 1: return f"{amount / GB:.1f}GB"
    if amount / MB > 1: return f"{amount / MB:.1f}MB"
    if amount / KB > 1: return f"{amount / KB:.1f}KB"
    return f"{amount} bytes"


class Memory():
    def __init__(self):
        self.previous = None
        self.hpy = None

    def sample(self, message=""):
        import guppy
        import psutil
        import textwrap
        from microlog.api import debug

        if not self.hpy:
            self.hpy = guppy.hpy()
        sample = self.hpy.heap()
        diff = (sample - self.previous) if self.previous else ""

        debug(textwrap.dedent(f"""
## Python memory analysis {message}

System memory total: {toGB(psutil.virtual_memory().total)}<br>
System memory used: {toGB(psutil.virtual_memory().used)}<br>
Process memory size: {toGB(psutil.Process().memory_info().rss)}<br>
Heap Size: {toGB(sample.size)}

## Current heap snapshot
```
{sample.byrcs}
```

{'## Difference with previous snapshot' if self.previous else ''}
```
{diff}
```
        """))
        self.previous = sample

