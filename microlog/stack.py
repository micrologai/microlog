#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import collections
import os
import sys
import traceback

from microlog import config
from microlog import events
from microlog import symbols


class Call():
    indexToCallSite = {}
    callSiteToIndex = collections.defaultdict(lambda: len(Call.indexToCallSite))

    def __init__(self, when: float, threadId: int, callSite: CallSite, callerSite: CallSite, depth: int, duration: float = 0.0):
        self.when = when
        self.threadId = threadId
        self.callSite = callSite
        self.callerSite = callerSite
        self.depth = depth
        self.duration = duration

    @classmethod
    def unmarshall(cls, event) -> Call:
        # typical event: 
        _, threadIdIndex, callSiteIndex, callerIndex, depth, whenIndex, durationIndex = event
        return Call(
            symbols.get(whenIndex),
            symbols.get(threadIdIndex),
            Call.indexToCallSite[callSiteIndex],
            Call.indexToCallSite[callerIndex],
            depth,
            symbols.get(durationIndex)
        )

    def marshall(self, when, threadId, caller):
        when = when
        self.duration = when - self.when
        callSiteIndex = self.getCallSiteIndex()
        callerSiteIndex = caller.getCallSiteIndex() if caller else 0
        events.put((
            config.EVENT_KIND_CALL,
            symbols.index(threadId),
            callSiteIndex,
            callerSiteIndex,
            self.depth,
            symbols.index(round(self.when, 3)),
            symbols.index(round(self.duration, 3)),
        ))

    def getCallSiteIndex(self):
        call = (
            symbols.index(self.callSite.filename),
            self.callSite.lineno,
            symbols.index(self.callSite.name),
        )
        if not call in Call.callSiteToIndex:
            events.put((config.EVENT_KIND_CALLSITE, len(Call.indexToCallSite), *call))
        callSiteIndex = Call.callSiteToIndex[call]
        Call.indexToCallSite[callSiteIndex] = call
        return callSiteIndex

    def isSimilar(self, other: Call):
        return other and self.callSite.isSimilar(other.callSite) and self.callerSite.isSimilar(other.callerSite)

    def __eq__(self, other: Call):
        return other and self.callSite == other.callSite and self.callerSite == other.callerSite

    def __repr__(self):
        return f"<Call {self.callSite.name}@{self.callSite.lineno}>"

@config.memoize
def absolutePath(filename):
    return os.path.abspath(filename)

class CallSite():
    def __init__(self, filename, lineno, name):
        self.filename = absolutePath(filename)
        self.lineno = lineno
        self.name = name

    @classmethod
    def unmarshall(cls, event):
        _, callSiteIndex, filenameIndex, lineno, nameIndex = event
        filename = symbols.get(filenameIndex)
        name = symbols.get(nameIndex)
        callSite = CallSite(filename, lineno, name)
        Call.indexToCallSite[callSiteIndex] = callSite
        return callSite

    def isSimilar(self, other: CallSite):
        return other and self.filename == other.filename and self.lineno == other.lineno and self.name == other.name

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return f"<CallSite {self.filename}:{self.name}:{self.lineno}>"


class Stack():
    def __init__(self, when=0, threadId=0, startFrame=None) -> None:
        self.when = when or events.now()
        self.calls = []
        if startFrame:
            callerSite = None
            stack = self.walkStack(startFrame)
            for depth, frameLineno in enumerate(stack):
                if self.skip(*frameLineno):
                    break
                callSite = self.callSiteFromFrame(*frameLineno)
                self.calls.append(
                    Call(when, threadId, callSite, callerSite, depth, 0)
                )
                callerSite = callSite
            
    def walkStack(self, startFrame):
        stack = [
            (frame, lineno)
            for frame, lineno in reversed(list(traceback.walk_stack(startFrame)))
            if not self.ignore(frame)
        ]
        return stack
            
    def callSiteFromFrame(self, frame, lineno):
        filename = frame.f_globals.get("__file__", "")
        module = frame.f_globals.get("__name__", "")
        if module == "__main__":
            module = sys.argv[0].replace(".py", "").replace("/", ".")
        instance = frame.f_locals["self"] if "self" in frame.f_locals else None
        clazz = ""
        if instance:
            clazz = instance.__class__.__name__
            module = instance.__module__
        name = frame.f_code.co_name
        return CallSite(filename, lineno, f"{module}.{clazz}.{name}")
        
    def ignore(self, frame):
        module = frame.f_globals.get("__name__", "")
        return module in ["microlog", "importlib"] or module.startswith("importlib.")

    def skip(self, frame, lineno):
        module = frame.f_globals.get("__name__", "")
        return module in ["microlog.stats", "microlog.threads", "microlog.config", "microlog.threads.tracer"]

    def __iter__(self):
        return iter(self.calls)

    def __len__(self):
        return len(self.calls)
    
    def __getitem__(self, index):
         return self.calls[index]

    def __repr__(self):
        calls = ", ".join(map(str, self.calls))
        return f"<Stack {calls}>"
