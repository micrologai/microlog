#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

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
    - start(): Starts the background thread. Sets it as a daemon thread and initializes the stack trace and main thread ID.
    - getMainStackFrame(): Gets the stack frame for the main thread.
    - tick(): Runs every `delay` seconds. Merges the current stack trace with a new one generated from the main stack frame. 
    - getStack(): Generates a new stack trace with the given timestamp and starting frame. 
    - merge(): Synchronizes two stack traces by updating timestamps and caller information.
    - stop(): Generates a final stack trace with the current timestamp.
    """
    def start(self) -> None:
        self.setDaemon(True)
        self.stack = stack.Stack()
        self.mainThread = threading.currentThread().ident
        self.delay = settings.current.traceDelay
        return threads.BackgroundThread.start(self)

    def getMainStackFrame(self):
        """
        Gets the stack frame for the main thread.

        Parameters: 
        - self: The Tracer object.

        Functionality:
        - Iterates through the stack frames of all threads.
        - Returns the stack frame for the thread with ID matching self.mainThread.
        """
        for ident, frame in sys._current_frames().items():
            if ident == self.mainThread:
                return frame

    def tick(self) -> None:
        """
        tick(): Runs every `delay` seconds. Generates a call stack sample.
        """
        self.sample()

    def sample(self, function=None) -> None:
        """
        merge(): Merges the current stack trace with a new one generated from the main stack frame.  

        Parameters:
        - function: The function to add to the current stack trace
        """
        self.merge(self.getStack(events.now(), self.getMainStackFrame(), function))

    def getStack(self, when, frame, function):
        """
        getStack(): Generates a new stack trace with the given timestamp and starting frame.  

        Parameters:
        - when: The timestamp for the new stack trace. 
        - frame: The starting frame for the new stack trace.
        - function: The function to add to the current stack trace

        Functionality:
        - Returns a new Stack object representing a stack trace with the given timestamp and starting frame.
          When function is not None, add it to the current stack. This is used when tracing a function.
        """
        currentStack = stack.Stack(when, frame)
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
            call = stack.Call(when, callSite, top.callSite, top.depth + 1, 0)
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

    def merge(self, stack: stack.Stack):
        """
        Synchronizes two stack traces by updating timestamps and caller information.  

        Parameters:
        - self: The Tracer object. 
        - stack: The new stack trace to merge with the current one.

        Functionality:
        - Iterates over the current stack trace and the new one call by call.
        - If two calls are the same, updates the timestamp of the new call to match the old one.
        - Otherwise, "marshalls" the old call by passing it the timestamp and caller of the new call.
        - Handles any remaining old calls by marshalling them with the last new call's timestamp and caller.
        - Finally, updates self.stack to the new stack.
        """
        caller = None
        for call1, call2 in zip(self.stack, stack):
            if call1 == call2:
                call2.when = call1.when
            else:
                call1.marshall(stack.when, caller)
            caller = call1
        if self.stack and len(self.stack) > len(stack):
            caller = self.stack[len(stack) - 1]
            for call in self.stack[len(stack):]:
                call.marshall(stack.when, caller)
                caller = call
        self.stack = stack

    def stop(self):
        """
        stop(): Generates a final stack trace with the current timestamp.  

        Parameters: 
        - self: The Tracer object.

        Functionality:
        - Calls merge() to synchronize the current stack trace with a new empty one with the current timestamp.
        """
        self.merge(stack.Stack(events.now()))

    
