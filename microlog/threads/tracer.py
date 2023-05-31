#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict

import inspect
import sys
import threading

from microlog import settings
from microlog import events
from microlog import stack
from microlog import threads

class Tracer(threads.BackgroundThread):
    """
    Tracer class that runs in a background thread and periodically generates stack traces.

    Parameters:
    - delay: The delay in seconds between generating stack traces.

    Functionality:
    - Starts a background daemon thread running tick() at a regular interval.
    - For each thread, merges the current stack trace with a new one.
    - At the end, generates a final stack trace with the current timestamp.
    """
    def start(self) -> None:
        self.setDaemon(True)
        self.stacks = defaultdict(stack.Stack)
        self.delay = settings.current.traceDelay
        return threads.BackgroundThread.start(self)

    def tick(self) -> None:
        """
        Runs every `delay` seconds. Generates a call stack sample.
        """
        self.sample()

    def sample(self, function=None) -> None:
        """
        Samples all threads.

        Parameters:
        - function: The function to add to the current stack trace, when using a decorator.
        """
        for threadId, frame in sys._current_frames().items():
            try:
                stack = self.getStack(events.now(), threadId, frame, function)
                self.merge(threadId, stack)
            except Exception as e:
                pass

    def getStack(self, when, threadId, frame, function):
        """
        Generates a new stack trace with the given timestamp and starting frame.  

        Parameters:
        - when: The timestamp for the new stack trace. 
        - frame: The starting frame for the new stack trace.
        - function: The function to add to the current stack trace
        """
        currentStack = stack.Stack(when, threadId, frame)
        if function:
            filename = inspect.getfile(function)
            lineno = inspect.getsourcelines(function)[1]
            module = inspect.getmodule(function).__name__
            if module == "__main__":
                module = sys.argv[0].replace(".py", "").replace("/", ".")
            clazz = self.getClassForMethod(function)
            name = function.__name__
            callSite = stack.CallSite(filename, lineno, f"{module}.{clazz}.{name}")
            top = currentStack.calls[-1]
            call = stack.Call(when, threadId, callSite, top.callSite, top.depth + 1, 0)
            currentStack.calls.append(call)
        return currentStack

    def getClassForMethod(self, method):
        if inspect.ismethod(method):
            for cls in inspect.getmro(method.__self__.__class__):
                if cls.__dict__.get(method.__name__) is method:
                    return cls.__name__
            method = method.__func__
        if inspect.isfunction(method):
            cls = getattr(inspect.getmodule(method),
                        method.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
            if isinstance(cls, type):
                return cls.__name__
        return ""

    def merge(self, threadId: int, stack: stack.Stack):
        """
        Synchronizes two stack traces by updating timestamps and caller information.  

        Parameters:
        - self: The Tracer object. 
        - threadId: The thread identifier for the stack.
        - stack: The new stack trace to merge with the current one.

        Functionality:
        - Iterates over the current stack trace and the new one call by call.
        - If two calls are the same, updates the timestamp of the new call to match the old one.
        - Otherwise, "marshalls" the old call by passing it the timestamp and caller of the new call.
        - Handles any remaining old calls by marshalling them with the last new call's timestamp and caller.
        - Finally, updates self.stacks to the new stack.
        """
        caller = None
        previousStack = self.stacks[threadId]
        for call1, call2 in zip(previousStack, stack):
            if call1 == call2:
                call2.when = call1.when
            else:
                call1.marshall(stack.when, threadId, caller)
            caller = call1
        if previousStack and len(previousStack) > len(stack):
            caller = previousStack[len(stack) - 1]
            for call in previousStack[len(stack):]:
                call.marshall(stack.when, threadId, caller)
                caller = call
        self.stacks[threadId] = stack

    def stop(self):
        """
        Generates a final stack trace with the current timestamp.  
        """
        threadId = threading.current_thread().ident
        self.merge(threadId, stack.Stack(events.now(), threadId))

    
