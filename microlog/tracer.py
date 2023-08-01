#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import collections

import gc
import inspect
import logging
import os
import signal
import sys
import threading
from time import time, sleep

from microlog import config
from microlog import log
from microlog import warn
from microlog import debug
from microlog import info
from microlog import error
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
        import psutil # type: ignore
        self.daemon = True
        self.running = False
        self.lastCpuSample = (log.log.now(), psutil.Process().cpu_times())
        self.delay = config.TRACER_STATUS_DELAY
        self.tick(log.log.now())

    def checkMemory(self, memory):
        gb = int(memory / GB)
        if gb > StatusGenerator.memoryWarning:
            StatusGenerator.memoryWarning = gb
            warn(f"WARNING: Python process memory grew to {memory / GB:.1f} GB")
    
    def tick(self, when) -> None:
        import psutil # type: ignore
        vm = psutil.virtual_memory()
        process = psutil.Process()
        systemCpu = psutil.cpu_percent() / psutil.cpu_count()
        memoryTotal = vm.total
        memoryFree = vm.free
        with process.oneshot():
            memory = process.memory_info()
            cpuTimes = process.cpu_times()

        def getCpu():
            lastCpuSampleTime, lastCpuTimes = self.lastCpuSample
            user = cpuTimes.user - lastCpuTimes.user
            system = cpuTimes.system - lastCpuTimes.system
            duration = when - lastCpuSampleTime
            cpu = min(100, (user + system) * 100 / duration) if duration else 0
            self.lastCpuSample = (when, cpuTimes)
            return cpu

        def getMemory():
            self.checkMemory(memory.rss)
            return memory.rss

        cpu = getCpu()
        memory = getMemory()

        log.log.addStatus(Status(
            when,
            cpu,
            systemCpu,
            memory,
            memoryTotal,
            memoryFree,
            len(sys.modules),
        ))

    def stop(self):
        self.tick(log.log.now())
        self.tick(log.log.now())


class Tracer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.statusGenerator = StatusGenerator()
        self.openFiles = {}
        self.running = False

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
        self.delay = config.TRACER_SAMPLE_DELAY
        if not self.delay:
            return
        self.setDaemon(True)
        self.stacks = collections.defaultdict(Stack)
        self.track_print()
        self.track_logging()
        self.track_gc()
        self.track_files()
        self.lastSample = 0
        self.lastStatus = 0
        self.sampleCount = 0
        self.running = True
        self.setupTimer()
    
    def setupTimer(self):
        try:
            # The peferred choice as this is the least amount of overhead 
            # Only works on Linux, UNIX, and MacOSs
            signal.signal(config.TRACER_SIGNAL_KIND, self.signal_handler)
            signal.setitimer(config.TRACE_TIMER_KIND, self.delay)
            info(f"Microlog: Using a signal timer with a sample delay of {self.delay}s")
            return
        except Exception as e:
            error(f"Microlog: Cannot use a signal timer: {e}")

        try:
            # The second-best choice, use a thread that sleeps
            # Does not work on PyScript/PyOdide as WebAssembly makes threads hard
            threading.Thread.start(self) # use thread if signals do not work
            info(f"Microlog: Using a background thread with a sample delay of {self.delay}s")
            return 
        except Exception as e:
            error(f"Microlog: Cannot use a background thread timer: {e}")

        try:
            # The final choice, this is needed for PyScript.
            # This has serious overhead, making Python run around 4X slower.
            sys.setprofile(lambda frame, event, arg: self.sample() if event == "call" else None)
            info(f"Microlog: Using sys.setprofile with a sample delay of {self.delay}s")
            return
        except Exception as e:
            error(f"Microlog: Cannot use a sys.profile timer: {e}")


    def signal_handler(self, sig, frame):
        try:
            self.sample()
            signal.setitimer(signal.ITIMER_PROF, self.delay)
        except:
            pass

    def profile(self, frame, event, arg, delay=config.TRACER_SAMPLE_DELAY):
        # This is to generate a timer if signals don't work (on PyScript?)
        # Needs the following during start:
        #  - self.lastProfile = log.log.now()
        #  - sys.setprofile(self.profile)
        if self.running and event == "c_exception":
            now = time()
            if now - self.lastProfile > delay:
                self.sample()
                self.lastProfile = time()
            return self.profile

    def run(self) -> None:
        while self.running:
            self.tick(log.log.now())
            sleep(self.delay)

    def track_gc(self):
        self.gc_info = {
            "duration": 0.0,
            "count": 0,
            "collected": 0,
            "uncollectable": 0,
        }
        gc.callbacks.append(self.gc_ran)
        
    def gc_ran(self, phase, info):
        if not self.running:
            return
        if phase == "start":
            self.gc_info["start"] = time()
        elif phase == "stop":
            duration = time() - self.gc_info["start"]
            self.gc_info["duration"] += duration
            self.gc_info["count"] += 1
            self.gc_info["collected"] += info["collected"]
            self.gc_info["uncollectable"] += info["uncollectable"]
            if duration > 1.0:
                debug(f"GC took {duration:.1}s for {info['collected']} objects.")

    def track_files(self):
        original_open = open
        def microlog_open(
            file,
            mode = "r",
            buffering = -1,
            encoding = None,
            errors = None,
            newline = None,
            closefd = True,
            opener = None,
        ):
            io = original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
            start = log.log.now()
            self.openFiles[io] = (io, start, inspect.stack()) 
            self.sample()

            if closefd:
                original_close = io.close
                def close():
                    original_close()
                    del self.openFiles[io]
                io.close = close

                original__exit__ = io.__exit__
                def __exit__():
                    original__exit__()
                    del self.openFiles[io]
                    io.__exit__ = __exit__

            return io
        __builtins__["open"] = microlog_open

    def track_print(self):
        self.original_print = print
        def microlog_print(
            *values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            file=None,
            flush=False,
        ) -> None: 
            self.original_print(*values, sep=sep, end=end, file=file, flush=flush)
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

    def tick(self, when) -> None:
        """
        Runs every `delay` seconds. Generates a call stack sample.
        """
        self.sample()
        self.generateStatus(when)

    def generateStatus(self, when):
        if when - self.lastStatus < config.TRACER_STATUS_DELAY:
            return
        self.lastStatus = when
        self.statusGenerator.tick(when)

    def sample(self, function=None) -> None:
        """
        Samples all threads.

        Parameters:
        - function: The function to add to the current stack trace, when using a decorator.
        """
        if not self.running:
            return
        when = log.log.now()
        if when - self.lastSample < config.TRACER_STATUS_DELAY:
            return
        self.sampleCount += 1
        self.lastSample = when
        frames = sys._current_frames()
        for threadId, frame in frames.items():
            if threadId != self.ident:
                self.merge(threadId, self.getStack(when, threadId, frame, function))
        for threadId in list(self.stacks.keys()):
            if threadId not in frames:
                self.merge(threadId, Stack(log.log.now(), threadId))
                del self.stacks[threadId]
        self.generateStatus(when)

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
        self.running = False
        if self.delay:
            try:
                # cancel the most recent signal timer
                signal.setitimer(signal.ITIMER_PROF, 0)
                time.sleep(self.delay)
            except:
                pass
            self.addFinalStack()
            self.addOpenFilesWarning()
            self.showStats()
    
    def addOpenFilesWarning(self):
        if self.openFiles:
            def shortFile(filename):
                parts = filename.split("/")
                if parts[-1] == "__init__.py":
                    parts.pop()
                return parts[-1]

            def link(frame):
                filename = frame.filename
                lineno = frame.lineno
                return f"<a href=vscode://file/{filename}:{lineno}:1>{shortFile(filename)}:{lineno}</a>"

            files = "\n".join([
                f" - At {when:.2f}s: {file.name} mode={file.mode} {link(stack[1])}"
                for file, when, stack in self.openFiles.values()
            ])
            warn(f"""
                # File Descriptors Leaked
                Found {len(self.openFiles)} files that were opened, but never closed:
                {files}
                """)
    
    def addFinalStack(self):
        now = log.log.now()
        self.statusGenerator.tick(now)
        for threadId in sys._current_frames():
            if threadId != self.ident:
                self.merge(threadId, Stack(now, threadId))
        self.generateStatus(now)
     
    def interesting(self, obj: any) -> bool:
        BUILTIN_MODULES = set([
            "http", "_frozen_importlib", "_frozen_importlib_external", "builtins",
            "weakref", "_weakrefset", "functools", "threading", "re", "__future__", "socketserver",
            "_thread", "encodings.utf_8", "os", "operator", "calendar", "email.charset", "email._policybase",
            "json.encoder", "json.decoder", "_json", "string", "psutil", "appdata", "pathlib", "ast",
            "itertools", "types", "collections", "_collections", "_abc", "typing", "psutil._common",
            "microlog", "microlog.models", "microlog.server", "microlog.tracer", "microlog.api", "microlog.log",
            "logging", "_io", "_sitebuiltins", "traceback", "_distutils_hack", "reprlib", "random",
        ])
        BASIC_TYPES = (
            Exception, list, dict, tuple, set, str, int, float, bool, type(None),
        )
        return not obj.__class__.__module__ in BUILTIN_MODULES and not inspect.isclass(obj) and not isinstance(obj, BASIC_TYPES)

    def getFile(self, moduleName):
        try:
            return inspect.getfile(sys.modules[moduleName])
        except:
            return sys.argv[0]

    def getActualModuleName(self, moduleName):
        name, _ext = os.path.splitext(self.getFile(moduleName))
        parts = name.split(os.path.sep)
        for n, part in enumerate(parts):
            if part.startswith("python"):
                return ".".join(parts[n + 1:]).replace("site-packages.", "")
        return ".".join(parts)
    
    def showStats(self):
        now = log.log.now()
        gc.collect()
        objects = [obj for obj in gc.get_objects() if self.interesting(obj)]
        typeCounts = collections.Counter(type(obj).__name__ for obj in objects)
        top10Types = dict(typeCounts.most_common(10))
        top10 = []
        for obj in objects:
            typeName = type(obj).__name__
            if typeName in top10Types:
                del top10Types[typeName]
                top10.append(obj)
        top10.sort(key=lambda obj: -typeCounts[type(obj).__name__])
        alive = "\n".join([
            f" - {typeCounts[type(obj).__name__]} instance{'s' if typeCounts[type(obj).__name__] > 1 else ''} of {self.getActualModuleName(obj.__class__.__module__)}.{obj.__class__.__name__}{self.getReferrers(obj, objects)}"
            for obj in top10
        ])
        leaks = f"# Possible Memory Leaks\nFound {len(objects):,} relevant leak{'s' if len(objects) > 1 else ''}. Here is the top 10:\n{alive}" if objects else ""
        uncollectable = f"A total of {self.gc_info['uncollectable']:,} objects were leaked (uncollectable) during runtime." if self.gc_info["uncollectable"] else ""
        count = self.gc_info["count"]
        count = "once" if count == 1 else f"{count} times"
        duration = self.gc_info["duration"]
        percentage = self.gc_info["duration"] / now * 100
        average = self.gc_info["duration"] / self.gc_info["count"] if self.gc_info["count"] else 0.0
        (error if leaks else debug)(f"""
# General Statistics
- Performed {self.sampleCount} samples
# GC Statistics
GC ran {count} for {duration:.3f}s ({percentage:.1f}% of {now:.3f}s), averaging {average:.3f}s per collection.
In total, {self.gc_info["collected"]:,} objects were collected.
{uncollectable}
{leaks}""")

    def describeReference(self, obj, value):
        if isinstance(obj, dict):
            for key in obj:
                if obj[key] is value:
                    if "__name__" in obj and "__package__" in obj and "__spec__" in obj:
                        moduleName = obj['__name__']
                        filename = os.path.abspath(self.getFile(moduleName))
                        link = f"<a style='color:red' href=vscode://file/{filename}:{1}:1>{self.getActualModuleName(moduleName)}</a>"
                        return f"\n    - see global variable '{key}' in module {link}"
                    return ""
        return ""

    def getReferrers(self, obj, objects):
        if obj is objects:
            return ""
        __checkLeaks_refs__ = gc.get_referrers(obj)
        for __checkLeaks_ref__ in __checkLeaks_refs__:
            if __checkLeaks_ref__ in [objects, __checkLeaks_refs__]:
                continue
            if isinstance(__checkLeaks_ref__, dict) and ("__checkLeaks__" in __checkLeaks_ref__ or "__checkLeaks_ref__" in __checkLeaks_ref__):
                continue
            return self.describeReference(__checkLeaks_ref__, obj)
        return ""

