#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Tracer module for Microlog."""

from __future__ import annotations

import collections
import gc
import inspect
import logging
import os
import sys
import threading
import time
from typing import Any
from typing import Callable

import psutil

from microlog import api
from microlog import config
from microlog.models import Stack
from microlog.models import recording


class StatusGenerator(threading.Thread):
    """Background thread that periodically samples system status and updates the recording."""

    def __init__(self) -> None:
        """Initialize StatusGenerator and start sampling."""
        threading.Thread.__init__(self)
        self.daemon: bool = True
        self.running: bool = False
        self.object_count: int = 0
        self.last_cpu_sample: tuple[float, Any] = (
            api.now(),
            psutil.Process().cpu_times(),
        )
        self.delay: float = config.TRACER_STATUS_DELAY
        self.memory_sample: tuple[int, int, int, int] = (0, 0, 0, 0)
        self.process: psutil.Process = psutil.Process()
        self.last_memory_sample_time: float = 0
        self.sample(api.now())
        self.start()

    def start(self) -> None:
        """Start the status sampling thread."""
        self.running = True
        threading.Thread.start(self)

    def run(self) -> None:
        """Run the status sampling loop."""
        while self.running:
            self.sample(api.now())
            time.sleep(self.delay)

    def sample(self, when: float) -> None:
        """Sample CPU and memory and update the recording."""
        cpu, system_cpu = self.get_cpu_details(when)
        memory_usage, memory_total, memory_free, object_count = self.get_memory_details(when)
        recording.add_status(
            when,
            cpu,
            system_cpu,
            memory_usage,
            memory_total,
            memory_free,
            len(sys.modules),
            object_count,
        )

    def get_cpu_details(self, when: float) -> tuple[float, float]:
        """Get CPU usage details."""
        try:
            system_cpu = psutil.cpu_percent() / float(psutil.cpu_count() or 1)
            cpu_times = self.process.cpu_times()
            last_cpu_sample_time, last_cpu_times = self.last_cpu_sample
            user = cpu_times.user - last_cpu_times.user
            system = cpu_times.system - last_cpu_times.system
            duration = when - last_cpu_sample_time
            cpu = min(100, (user + system) * 100 / duration) if duration else 0
            self.last_cpu_sample = (when, cpu_times)
            return cpu, system_cpu
        except TypeError:
            return 0.0, 0.0  # this platform does not support cpu times

    def get_memory_details(self, when: float) -> tuple[int, int, int, int]:
        """Get memory usage details."""
        if (
            not self.last_memory_sample_time
            or when - self.last_memory_sample_time >= config.TRACER_MEMORY_DELAY
        ):
            vm = psutil.virtual_memory()
            memory_total = vm.total
            memory_free = vm.free
            memory = self.process.memory_info()
            self.last_memory_sample_time = when
            objects = gc.get_objects(generation=2)
            self.memory_sample = memory.rss, memory_total, memory_free, len(objects)
            del objects
        return self.memory_sample

    def stop(self) -> None:
        """Stop the status sampling thread and perform final ticks."""
        self.running = False
        self.sample(api.now())
        self.sample(api.now())


class Tracer(threading.Thread):
    """Tracer class that runs in a background thread and periodically generates stack traces."""

    memory_warning: int = 32

    def __init__(self) -> None:
        """Initialize Tracer and start background thread."""
        threading.Thread.__init__(self)
        self.gc_info: dict[str, Any] = { }
        self.delay: float = 0.0
        self.open_files: dict[Any, tuple[Any, float, list[Any]]] = {}
        self.original_write: Callable[..., None] = sys.stdout.write
        self.running: bool = False
        self.already_tracked_imports: set[str] = set()
        self.start()

    def start(self) -> None:
        """Start the tracer thread and initialize tracking."""
        self.delay = config.TRACER_SAMPLE_DELAY
        if not self.delay:
            return
        self.pandas_count: int = 0
        self.polars_count: int = 0
        self.daemon: bool = True
        self.stacks: dict[int, Stack] = collections.defaultdict(Stack)
        self.track_print()
        self.track_logging()
        self.track_gc()
        self.last_profile: float = 0
        self.running = True
        self.new_stack: Stack | None = None
        threading.Thread.start(self)

    def run(self) -> None:
        """Run the tracer sampling loop."""
        while self.running:
            self.sample(api.now())
            time.sleep(self.delay)

    def track_gc(self) -> None:
        """Track garbage collection events."""
        self.gc_info = {
            "duration": 0.0,
            "count": 0,
            "collected": 0,
            "uncollectable": 0,
        }
        gc.callbacks.append(self.gc_ran)

    def gc_ran(self, phase: str, info: dict[str, Any]) -> None:
        """Callback for GC events."""
        if not self.running:
            return
        if phase == "start":
            self.gc_info["start"] = time.time()
        elif phase == "stop":
            duration = time.time() - self.gc_info["start"]
            self.gc_info["duration"] += duration
            self.gc_info["count"] += 1
            self.gc_info["collected"] += info["collected"]
            self.gc_info["uncollectable"] += info["uncollectable"]

    def check_memory(self, memory: int) -> None:
        """Adjust sampling delay if memory usage exceeds warning threshold."""
        gb = int(memory / config.GB)
        if gb > self.memory_warning:
            self.memory_warning = gb
            multiplier = gb / 10
            memory_adjusted_delay = config.TRACER_SAMPLE_DELAY * multiplier
            if memory_adjusted_delay > self.delay:
                self.delay = memory_adjusted_delay

    def track_print(self) -> None:
        """Track print statements and wrap the built-in print function."""
        def microlog_write(s: str) -> None:
            """Custom print function that logs output."""
            self.original_write(s)
            if s.strip():
                api.log(config.EVENT_KIND_INFO, s)

        setattr(sys.stdout, "write", microlog_write)

    def untrack_print(self) -> None:
        """Restore the original print function."""
        setattr(sys.stdout, "write", self.original_write)

    def track_logging(self) -> None:
        """Track logging events and wrap the logging handler."""

        class LogStreamHandler(logging.StreamHandler[Any]):
            """Custom logging handler that sends log records to Microlog."""

            def emit(self, record: logging.LogRecord) -> None:
                """Emit a log record to Microlog."""
                msg = f"{record.levelname}: {record.msg}"
                print(msg)
                api.log(record.levelno, msg)

        logging.getLogger().addHandler(LogStreamHandler())

    def sample(self, when:float) -> None:
        """
        Samples all threads and merges their stack traces.
        """
        if not self.running:
            return

        frames = {}
        try:
            frames = sys._current_frames()  # pylint: disable=protected-access

            # Process active threads
            for ident, frame in frames.items():
                if ident != self.ident:
                    self.merge(ident, Stack(when, frame))
                    del frame  # delete reference

            # Clean up stacks for terminated threads
            terminated_threads = set(self.stacks.keys()) - set(frames.keys())
            for thread_id in terminated_threads:
                self.merge(thread_id, Stack(when))
                del self.stacks[thread_id]
        finally:
            if frames:
                del frames  # delete reference

    def merge(self, thread_id: int, stack: Stack) -> None:
        """
        Synchronizes two stack traces by updating timestamps and caller information.

        Parameters:
        - thread_id: The thread identifier for the stack.
        - stack: The new stack trace to merge with the current one.
        """
        previous_stack: Stack = self.stacks[thread_id]
        stack_ended = False
        now = stack.when if stack else api.now()
        depth = 0
        for call1, call2 in zip(previous_stack, stack):
            call1.duration = now - call1.when
            if not stack_ended and call1 == call2:
                call2.when = call1.when
                call2.duration = call1.duration
            else:
                recording.add_call(
                    call1.when,
                    thread_id,
                    call1,
                    previous_stack[depth - 1],
                    depth,
                    call1.duration,
                )
                stack_ended = True
            depth += 1
        now = stack.when if stack else api.now()
        if previous_stack and len(previous_stack) > len(stack):
            for call in previous_stack[len(stack) :]:
                recording.add_call(
                    call.when,
                    thread_id,
                    call,
                    previous_stack[depth - 1],
                    depth,
                    now - call.when,
                )
                depth += 1
        self.stacks[thread_id] = stack

    def stop(self) -> None:
        """
        Generates a final stack trace for all threads with the current timestamp
        and logs statistics.
        """
        self.running = False
        try:
            self.add_final_stack()
            self.add_open_files_warning()
            self.show_stats()
            self.untrack_print()
        except Exception as e: # pylint: disable=broad-except
            print("Microlog: Error while stopping tracer", e)

    def add_open_files_warning(self) -> None:
        """Log a warning for any files that were opened but not closed."""
        if self.open_files:
            def link(frame: Any) -> str:
                """Create a clickable link for a frame."""
                filename = frame.filename
                lineno = frame.lineno
                return api.create_link(filename, lineno)

            files = "\n".join(
                [
                    f" - At {when:.2f}s: {file.name} mode={file.mode} {link(stack[1])}"
                    for file, when, stack in self.open_files.values()
                ]
            )
            api.log(config.EVENT_KIND_WARN, f"""
                # File Descriptors Leaked
                Found {len(self.open_files)} files that were opened, but never closed:
                {files}
                """)

    def add_final_stack(self) -> None:
        """Generate a final stack trace for all threads."""
        now = api.now()
        for thread_id in sys._current_frames(): # pylint: disable=protected-access
            if thread_id != self.ident:
                self.merge(thread_id, Stack(now))

    def interesting(self, obj: Any) -> bool:
        """Determine if an object is interesting for leak detection."""
        try:
            return (
                obj.__class__.__module__ not in config.BUILTIN_MODULES
                and not inspect.isclass(obj)
                and not isinstance(obj, config.BASIC_TYPES)
            )
        except Exception: # pylint: disable=broad-except
            return False

    def get_file(self, module_name: str) -> str:
        """Get the file path for a module name."""
        try:
            return inspect.getfile(sys.modules[module_name])
        except Exception: # pylint: disable=broad-except
            return sys.argv[0]

    def get_actual_module_name(self, module_name: str) -> str:
        """Get the actual module name from a file path."""
        name, _ext = os.path.splitext(self.get_file(module_name))
        parts = name.split(os.path.sep)
        for n, part in enumerate(parts):
            if part.startswith("python"):
                return ".".join(parts[n + 1 :]).replace("site-packages.", "")
        return ".".join(parts)

    def show_stats(self) -> None:
        """Log statistics about garbage collection and possible memory leaks."""
        now = api.now()
        gc.collect()
        objects = [obj for obj in gc.get_objects() if self.interesting(obj)]
        type_counts = collections.Counter(type(obj).__name__ for obj in objects)
        top100_types = dict(type_counts.most_common(100))
        top100: list[Any] = []
        for obj in objects:
            type_name = type(obj).__name__
            if type_name in top100_types:
                del top100_types[type_name]
                top100.append(obj)
        top100.sort(key=lambda obj: -type_counts[type(obj).__name__])
        alive = "\n".join(
            [
                f" - {type_counts[type(obj).__name__]} instance"
                f"{'s' if type_counts[type(obj).__name__] > 1 else ''} of "
                f"{self.get_actual_module_name(obj.__class__.__module__)}."
                f"{obj.__class__.__name__}"
                for obj in top100
            ]
        )
        leaks = (
            f"# Possible Memory Leaks\nFound {len(objects):,} relevant leak"
            f"{'s' if len(objects) > 1 else ''}. Here are the top 100:\n{alive}"
            if objects
            else ""
        )
        uncollectable = (
            f"A total of {self.gc_info['uncollectable']:,} objects were leaked "
            "(uncollectable) during runtime."
            if self.gc_info["uncollectable"]
            else ""
        )
        count = self.gc_info["count"]
        count = "once" if count == 1 else f"{count} times"
        duration = self.gc_info["duration"]
        percentage = self.gc_info["duration"] / now * 100
        average = (
            self.gc_info["duration"] / self.gc_info["count"]
            if self.gc_info["count"]
            else 0.0
        )

        kind = config.EVENT_KIND_ERROR if leaks else config.EVENT_KIND_DEBUG
        api.log(kind, f"""
# General Statistics
# GC Statistics
GC ran {count} for {duration:0.3f}s ({percentage:0.1f}% of {now:.3f}s),
averaging {average:.3f}s per collection.
In total, {self.gc_info["collected"]:,} objects were collected.
{uncollectable}
{leaks}
""")
