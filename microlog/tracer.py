#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict

import gc
import inspect
import logging
import sys
import threading
import time

from microlog import config
from microlog import log
from microlog.models import Status
from microlog.models import Call
from microlog.models import CallSite
from microlog.models import Stack


KB = 1024
MB = KB * KB
GB = MB * KB

class StatusGenerator():
    memoryWarning = 0

    def __init__(self):
        import psutil
        self.daemon = True
        self.lastCpuSample = (log.log.now(), psutil.Process().cpu_times())
        self.delay = config.statusDelay
        self.tick()

    def checkMemory(self, memory):
        gb = int(memory / GB)
        if gb > StatusGenerator.memoryWarning:
            from microlog.api import warn
            StatusGenerator.memoryWarning = gb
            warn(f"WARNING: Python process memory grew to {memory / GB:.1f} GB")
    
    def tick(self) -> None:
        import psutil
        vm = psutil.virtual_memory()
        process = psutil.Process()
        systemCpu = psutil.cpu_percent() / psutil.cpu_count()
        memoryTotal = vm.total
        memoryFree = vm.free
        now = log.log.now()
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

        cpu = getCpu()
        memory = getMemory()

        log.log.addStatus(Status(
            log.log.now(), 
            cpu,
            systemCpu,
            memory,
            memoryTotal,
            memoryFree,
            len(sys.modules),
        ))

    def stop(self):
        self.tick()
        self.tick()


class Tracer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.statusGenerator = StatusGenerator()

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
        from microlog import config
        self.setDaemon(True)
        self.stacks = defaultdict(Stack)
        self.delay = config.traceDelay
        self.track_print()
        self.track_logging()
        self.track_gc()
        self.lastStatus = 0
        self.running = True
        return threading.Thread.start(self)

    def run(self) -> None:
        while self.running:
            self.tick()
            time.sleep(self.delay)

    def track_gc(self):
        self.gc_info = {
            "duration": 0.0,
            "count": 0,
            "collected": 0,
        }
        gc.callbacks.append(self.gc_ran)
        
    def gc_ran(self, phase, info):
        from microlog.api import debug
        if phase == "start":
            self.gc_info["start"] = time.time()
        elif phase == "stop":
            duration = time.time() - self.gc_info["start"]
            self.gc_info["duration"] += duration
            self.gc_info["count"] += 1
            self.gc_info["collected"] += info["collected"]
            if duration > 1.0:
                debug(f"GC took {duration:.1}s for {info['collected']} objects.")

    def track_print(self):
        from microlog.api import info
        from microlog.api import error
        original_print = print
        def microlog_print(
            *values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            file=None,
            flush=False,
        ) -> None: 
            original_print(*values, sep=sep, end=end, file=file, flush=flush)
            if self.running:
                log = error if file == sys.stderr else info if file in [None, sys.stdout] else None
                if log:
                    log(" ".join(map(str, values)))
                self.sample()
        __builtins__["print"] = microlog_print

    def track_logging(self):
        tracer = self

        class LogStreamHandler(logging.StreamHandler):
            def __init__(self):
                logging.StreamHandler.__init__(self)
                self.setLevel(logging.DEBUG)
                self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

            def emit(self, record):
                from microlog.api import debug
                from microlog.api import info
                from microlog.api import warn
                from microlog.api import error
                message = self.format(record)
                if record.levelno == logging.INFO:
                    info(message)
                elif record.levelno == logging.DEBUG:
                    debug(message)
                elif record.levelno == logging.WARN:
                    warn(message)
                elif record.levelno == logging.ERROR:
                    error(message)
                tracer.sample()

        logging.getLogger().addHandler(LogStreamHandler())

    def tick(self) -> None:
        """
        Runs every `delay` seconds. Generates a call stack sample.
        """
        self.sample()
        from microlog import config
        from microlog import log
        when = log.log.now()
        if when - self.lastStatus > config.statusDelay:
            self.lastStatus = when
            self.statusGenerator.tick()

    def sample(self, function=None) -> None:
        """
        Samples all threads.

        Parameters:
        - function: The function to add to the current stack trace, when using a decorator.
        """
        from microlog import log
        when = log.log.now()
        frames = sys._current_frames()
        for threadId, frame in frames.items():
            if threadId != self.ident:
                self.merge(threadId, self.getStack(when, threadId, frame, function))
        for threadId in list(self.stacks.keys()):
            if threadId not in frames:
                self.merge(threadId, Stack(log.log.now(), threadId))
                del self.stacks[threadId]

    def getStack(self, when, threadId, frame, function):
        """
        Generates a new stack trace with the given timestamp and starting frame.  

        Parameters:
        - when: The timestamp for the new stack trace. 
        - frame: The starting frame for the new stack trace.
        - function: The function to add to the current stack trace
        """
        currentStack = Stack(when, threadId, frame)
        if function:
            filename = inspect.getfile(function)
            lineno = inspect.getsourcelines(function)[1]
            module = inspect.getmodule(function).__name__
            if module == "__main__":
                module = sys.argv[0].replace(".py", "").replace("/", ".")
            clazz = self.getClassForMethod(function)
            name = function.__name__
            callSite = CallSite(filename, lineno, f"{module}.{clazz}.{name}")
            currentStack.callSites.append(callSite)
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

    def merge(self, threadId: int, stack: Stack):
        """
        Synchronizes two stack traces by updating timestamps and caller information.  

        Parameters:
        - self: The Tracer object. 
        - threadId: The thread identifier for the stack.
        - stack: The new stack trace to merge with the current one.

        Functionality:
        - Iterates over the current stack trace and the new one call by call.
        - If two calls are the same, updates the timestamp of the new call to match the old one.
        - Otherwise, logs the old call.
        - Handles any remaining old calls by logging them.
        - Finally, updates self.stacks to the new stack.
        """
        previousStack = self.stacks[threadId]
        stackEnded = False
        now = stack.when if stack else log.log.now()
        depth = 0
        for call1, call2 in zip(previousStack, stack):
            call1.duration = now - call1.when
            if not stackEnded and call1 == call2:
                call2.when = call1.when
                call2.duration = call1.duration
            else:
                log.log.addCall(Call(call1.when, threadId, call1, previousStack[depth - 1], depth, call1.duration))
                stackEnded = True
            depth += 1
        if previousStack and len(previousStack) > len(stack):
            for call in previousStack[len(stack):]:
                log.log.addCall(Call(call.when, threadId, call, previousStack[depth - 1], depth, call.duration))
                depth += 1
        self.stacks[threadId] = stack

    def stop(self):
        """
        Generates a final stack trace for all threads with the current timestamp.  
        """
        from microlog import log
        from microlog.api import info
        self.statusGenerator.tick()
        self.running = False
        now = log.log.now()
        for threadId in sys._current_frames():
            if threadId != self.ident:
                self.merge(threadId, Stack(now, threadId))
        info(f"""
             GC ran {self.gc_info["count"]} times.
             Total time spent in GS was {self.gc_info["duration"]:.3}s, which is {self.gc_info["duration"] / now * 100:.2f}% of total runtime.
             Average collection took {self.gc_info["duration"] / self.gc_info["count"] if self.gc_info["count"] else 0.0:.3}s.
             A total of {self.gc_info["collected"]:,} objects were collected.
             """)


    
