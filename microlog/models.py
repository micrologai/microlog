#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import collections
import json
import os
import sys
import threading
import traceback


indexToSymbol = {}
indexToCallSite = {}

symbolToIndex = collections.defaultdict(lambda: len(indexToSymbol))
callSiteToIndex = collections.defaultdict(lambda: len(indexToCallSite))

lock = threading.Lock()

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
    def unmarshall(cls, event) -> Call:
        # typical event: 
        _, threadIdIndex, callSiteIndex, callerIndex, depth, whenIndex, durationIndex = event
        assert isinstance(threadIdIndex, int), "threadIdIndex should be a number"
        assert isinstance(callSiteIndex, int), "callSiteIndex should be a number"
        assert callSiteIndex in indexToCallSite, "callSiteIndex unknown"
        assert isinstance(callerIndex, int), "callerIndex should be a number"
        assert callerIndex in indexToCallSite, "callerIndex unknown"
        assert isinstance(depth, int), "depth should be a number"
        assert isinstance(whenIndex, int), "whenIndex should be a number"
        assert isinstance(durationIndex, int), "durationIndex should be a number"
        return Call(
            getSymbol(whenIndex),
            getSymbol(threadIdIndex),
            indexToCallSite[callSiteIndex],
            indexToCallSite[callerIndex],
            depth,
            getSymbol(durationIndex)
        )

    def marshall(self, when, threadId, caller):
        from microlog import log
        from microlog import config
        when = when
        self.duration = when - self.when
        callSiteIndex = self.getCallSiteIndex()
        callerSiteIndex = caller.getCallSiteIndex() if caller else 0
        log.put((
            config.EVENT_KIND_CALL,
            indexSymbol(threadId),
            callSiteIndex,
            callerSiteIndex,
            self.depth,
            indexSymbol(round(self.when, 3)),
            indexSymbol(round(self.duration, 3)),
        ))

    def getCallSiteIndex(self):
        from microlog import log
        from microlog import config
        call = (
            indexSymbol(self.callSite.filename),
            self.callSite.lineno,
            indexSymbol(self.callSite.name),
        )
        if not call in callSiteToIndex:
            log.put((config.EVENT_KIND_CALLSITE, len(indexToCallSite), *call))
        callSiteIndex = callSiteToIndex[call]
        indexToCallSite[callSiteIndex] = call
        return callSiteIndex

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
    def unmarshall(cls, event):
        _, callSiteIndex, filenameIndex, lineno, nameIndex = event
        assert isinstance(callSiteIndex, int), "callsiteIndex should be a number"
        assert isinstance(filenameIndex, int), "filenameIndex should be a number"
        assert isinstance(lineno, int), "lineno should be a number"
        assert isinstance(nameIndex, int), "nameIndex should be a number"
        filename = getSymbol(filenameIndex)
        name = getSymbol(nameIndex)
        callSite = CallSite(filename, lineno, name)
        indexToCallSite[callSiteIndex] = callSite
        return callSite

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
        self.when = when or log.now()
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
        filename = frame.f_globals.get("__file__", "").replace(os.path.expanduser("~"), "~")
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


class MarkerModel():
    def __init__(self, kind: int, when:float, message: str, stack:List[str]):
        self.when = when
        self.kind = kind
        self.message = message
        self.stack = stack
        self.duration = 0.1

    @classmethod
    def unmarshall(cls, event: list) -> MarkerModel:
        kind, when, messageIndex, stack = event
        assert isinstance(kind, int), "kind should be an int"
        assert isinstance(when, float), "when should be a float"
        assert isinstance(messageIndex, int), "messageIndex should be an int"
        assert isinstance(stack, list), f"stack should be a list, not {type(stack)}: {stack}"
        return MarkerModel(
            kind,
            when,
            getSymbol(messageIndex),
            [ getSymbol(index).replace("\\n", "\n") for index in stack ],
        )

    def marshall(self):
        from microlog import log
        log.put([
            self.kind,
            self.when,
            indexSymbol(self.message),
            [ indexSymbol(line) for line in self.stack[:-2] if not "microlog/microlog/__init__.py" in line ],
        ])


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
        assert isinstance(whenIndex, int), f"whenIndex should be an int, not {type(whenIndex)}: {whenIndex}"
        assert isinstance(dataIndex, int), f"dataIndex should be an int, not {type(dataIndex)}: {dataIndex}"
        assert isinstance(getSymbol(dataIndex), str), f"data symbol should be a str, not {type(getSymbol(dataIndex))}: {dataIndex}:{getSymbol(dataIndex)}"
        system, process, python = json.loads(getSymbol(dataIndex))
        systemCpu, systemMemoryTotal, systemMemoryFree= system
        cpu, memory = process
        moduleCount = python[0]
        return Status(
            getSymbol(whenIndex),
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
        from microlog import log
        from microlog import config
        log.put([
            config.EVENT_KIND_STATUS,
            indexSymbol(round(self.when, 3)),
            indexSymbol(json.dumps([
                [
                    round(self.system.cpu),
                    round(self.system.memoryTotal / GB, 1),
                    round(self.system.memoryFree / GB, 1),
                ],
                [
                    round(self.process.cpu),
                    round(self.process.memory / GB, 1),
                ],
                [
                    self.python.moduleCount,
                ]
            ])),
        ])

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

    def sample(self):
        import guppy
        import psutil
        from microlog.api import debug

        if not self.hpy:
            self.hpy = guppy.hpy()
        sample = self.hpy.heap()
        diff = (sample - self.previous) if self.previous else "None"

        debug(f"""
            # Python memory analysis 
            
            System memory total: {toGB(psutil.virtual_memory().total)}<br>
            System memory used: {toGB(psutil.virtual_memory().used)}<br>
            Process memory size: {toGB(psutil.Process().memory_info().rss)}<br>
            Heap Size: {toGB(sample.size)}
            
            ## Current heap snapshot
            ```
            {sample.byrcs}
            ```

            ## Difference with previous snapshot
            ```
            {diff}
            ```
        """)
        self.previous = sample

    def stop(self):
        pass


def indexSymbol(symbol):
    from microlog import log
    from microlog import config
    with lock:
        if isinstance(symbol, str):
            symbol = symbol.replace("\n", "\\n").replace("\"", "\\\"")
        if not symbol in symbolToIndex:
            log.put((
                config.EVENT_KIND_SYMBOL,
                symbolToIndex[symbol],
                symbol,
            ))
            indexToSymbol[symbolToIndex[symbol]] = symbol

        return symbolToIndex[symbol]


def unmarshallSymbol(event):
    # typical event: [0, 144, "inspect psutil"]
    assert isinstance(event[1], int), "symbol[1] should be an int"
    assert isinstance(event[2], (float, int, str)), f"symbol[2] should be a literal, not {type(event[2])}: {event[2]}"
    putSymbol(event[1], event[2])
    return event[2]


def putSymbol(index, symbol):
    with lock:
        if isinstance(symbol, str):
            symbol = symbol.replace("\n", "\\n")
        indexToSymbol[index] = symbol


def getSymbol(index):
    return indexToSymbol[index]


def start():
    pass


def clear():
    global indexToSymbol, indexToCallSite, symbolToIndex, callSiteToIndex
    indexToSymbol = {}
    indexToCallSite = {}
    symbolToIndex = collections.defaultdict(lambda: len(indexToSymbol))
    callSiteToIndex = collections.defaultdict(lambda: len(indexToCallSite))


def stop():
    clear()