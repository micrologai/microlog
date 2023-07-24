#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

from collections import defaultdict
import os
import sys
import traceback

from microlog import config

KB = 1024
MB = KB * KB
GB = MB * KB


def join(*numbers):
    return " ".join(str(n) for n in numbers)


def absolutePath(filename):
    return os.path.abspath(filename)
        

class Call():
    def __init__(self, when: float, threadId: int, callSite: CallSite, callerSite: CallSite, depth: int, duration: float = 0.0):
        self.when = round(when, 3)
        assert isinstance(callSite, CallSite), f"callSite should be a CallSite, not {type(callSite)}: {callSite}"
        self.threadId = threadId
        self.callSite = callSite
        self.callerSite = callerSite
        self.depth = depth
        self.duration = round(duration, 3)

    @classmethod
    def save(self, calls, lines, symbols):
        threadIds = defaultdict(lambda: len(threadIds))
        callSites = defaultdict(lambda: len(callSites))
        for call in calls:
            lines.append(
                f"{call.when} "
                f"{threadIds[call.threadId]} "
                f"{callSites[call.callSite]} "
                f"{callSites[call.callerSite]} "
                f"{call.depth} "
                f"{round(call.duration, 3)}"
            )
        lines.append(f"{config.EVENT_KIND_SECTION} {config.EVENT_KIND_CALL} Calls")
        CallSite.save(callSites.keys(), lines, symbols)

    @classmethod
    def load(self, line, callSites):
        when, threadId, callSiteIndex, callerSiteIndex, depth, duration = line.split()
        return Call(
            float(when),
            threadId,
            callSites[int(callSiteIndex)],
            callSites[int(callerSiteIndex)],
            int(depth),
            float(duration)
        )

    def isSimilar(self, other: Call):
        return other and self.callSite.isSimilar(other.callSite) and self.callerSite.isSimilar(other.callerSite)

    def __eq__(self, other: Call):
        return other and self.callSite == other.callSite and self.callerSite == other.callerSite

    def __hash__(self):
        return hash((self.callSite, self.callerSite))

    def __repr__(self):
        return f"<Call {self.callSite.name}@{self.callSite.lineno}>"

class CallSite():
    def __init__(self, filename, lineno, name):
        self.filename = absolutePath(filename)
        self.lineno = lineno or 0
        self.name = name

    @classmethod
    def save(self, callSites, lines, symbols):
        for n, callSite in enumerate(callSites):
            lines.append(
                f"{n} "
                f"{symbols[callSite.filename if callSite else '']} "
                f"{callSite.lineno if callSite else 0} "
                f"{symbols[callSite.name if callSite else '..']}"
            )
        lines.append(f"{config.EVENT_KIND_SECTION} {config.EVENT_KIND_CALLSITE} CallSites")

    @classmethod
    def load(self, line, symbols):
        index, filenameIndex, lineno, nameIndex = line.split()
        return index, CallSite(symbols[int(filenameIndex)], int(lineno), symbols[int(nameIndex)])

    def isSimilar(self, other: CallSite):
        return other and self.filename == other.filename and self.lineno == other.lineno and self.name == other.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return f"<CallSite {self.filename}:{self.name}:{self.lineno}>"


class Stack():
    def __init__(self, when=0, threadId=0, startFrame=None, index=0, callSites=None) -> None:
        from microlog import log
        self.index = index
        self.when = when or log.log.now()
        self.callSites = callSites or []
        if startFrame:
            for frameLineno in self.walkStack(startFrame):
                callSite = self.callSiteFromFrame(*frameLineno)
                if not callSite:
                    break
                callSite.when = self.when
                callSite.duration = 0.0
                self.callSites.append(callSite)
            
    @classmethod
    def save(self, stacks, lines, symbols):
        callSites = defaultdict(lambda: len(callSites))
        for stack, n in sorted(stacks.items(), key = lambda item: item[1]):
            lines.append(f"{n} {' '.join(str(callSites[call]) for call in stack.callSites)}")
        lines.append(f"{config.EVENT_KIND_SECTION} {config.EVENT_KIND_STACK} Stacks")
        CallSite.save(callSites, lines, symbols)

    @classmethod
    def load(self, line, callSites):
        parts = line.split()
        return Stack(when=0.0, index=int(parts[0]), callSites = [callSites[int(index)] for index in parts[1:]])

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
        return module in config.IGNORE_MODULES

    def __iter__(self):
        return iter(self.callSites)

    def __len__(self):
        return len(self.callSites)
    
    def __getitem__(self, index):
         return self.callSites[index]

    def __repr__(self):
        callSites = " ".join(callSite.name for callSite in self.callSites)
        return f"<Stack {self.index} {callSites}\n>"


class Marker():
    def __init__(self, kind: int, when:float, message: str, stack:Stack, duration: float=0.1):
        self.when = round(when, 3)
        self.kind = kind
        self.message = message
        self.stack = stack
        self.duration = duration

    @classmethod
    def save(self, markers, lines, symbols):
        stacks = defaultdict(lambda: len(stacks))
        for marker in markers:
            lines.append(
                f"{marker.kind} "
                f"{marker.when} "
                f"{symbols[marker.message]} "
                f"{stacks[marker.stack]} "
                f"{marker.duration}"
            )
        lines.append(f"{config.EVENT_KIND_SECTION} {config.EVENT_KIND_MARKER} Markers")
        Stack.save(stacks, lines, symbols)

    @classmethod
    def load(self, line, symbols, stacks):
        kind, when, messageIndex, stackIndex, duration = line.split()
        return Marker(
            int(kind), 
            float(when), 
            symbols[int(messageIndex)], 
            stacks[int(stackIndex)], 
            float(duration)
        )


class Status():
    def __init__(self, when, cpu, systemCpu, memory, memoryTotal, memoryFree, moduleCount):
        assert isinstance(when, float), f"when should be a float, not {type(when)}: {when}"
        self.when = round(when, 3)
        self.cpu = round(cpu)
        self.systemCpu = systemCpu
        self.memory = memory
        self.memoryTotal = memoryTotal
        self.memoryFree = memoryFree
        self.moduleCount = moduleCount
        self.duration = 0.0

    @classmethod
    def save(self, statuses, lines, symbols):
        for status in statuses:
            lines.append(
                f"{round(status.when, 3)} "
                f"{symbols[ join(round(status.cpu), round(status.systemCpu), status.memory, status.memoryTotal, status.memoryFree, status.moduleCount) ]}"
            )
        lines.append(f"{config.EVENT_KIND_SECTION} {config.EVENT_KIND_STATUS} Statuses")
        
    @classmethod
    def load(self, line, symbols):
        when, detailsIndex = line.split()
        cpu, systemCpu, memory, memoryTotal, memoryFree, moduleCount = symbols[int(detailsIndex)].split()
        return Status(
            float(when),
            float(cpu),
            float(systemCpu), 
            int(memory), 
            int(memoryTotal), 
            int(memoryFree), 
            int(moduleCount)
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

