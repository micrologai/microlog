#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

"""
Models for calls, stacks, and recording used by tracer, server, and ui. 
"""

from __future__ import annotations

import datetime
from functools import cache
import inspect
import logging
import os
import pickle
import sys
import traceback
from typing import Any
from typing import cast
from typing import overload
import urllib.error
import urllib.request

from microlog import config


KB: int = 1024
MB: int = KB * KB
GB: int = MB * KB

symbols: dict[str, str] = {}
absolute_paths: dict[str, str] = {}


def internalize(string: str) -> str:
    """Store and return a single instance of a string to save memory."""
    if string not in symbols:
        symbols[string] = string
    return symbols[string]

@cache
def absolute_path(filename: str) -> str:
    """Get the absolute path of a filename, resolving any symlinks."""
    return os.path.abspath(filename)

class Recording:
    """
    A Recording contains lists of Calls, Stacks, and Markers.

    Each Call represents a function/method call, with a CallSite
    representing the location of the call. A recording is saved using
    the save() method and loaded using the load() method.
    """

    def __init__(self) -> None:
        """Initialize an empty Recording."""
        self.application:str = ""
        self.calls: list[Call] = []
        self.markers: list[Marker] = []
        self.statuses: list[Status] = []

    def show_details(self, identifier: str) -> None:
        """Print details about the recording, including a link to view it."""
        url = f"{config.SERVER}#{identifier.replace(' ', '_')}"
        self.print_in_block(f"Microlog: {url}")

    def notify_server(self, identifier: str) -> None:
        """Notify the Microlog server that a new recording is available."""
        try:
            urllib.request.urlopen(f"{config.SERVER}/save/{identifier.replace(' ', '_')}")
        except urllib.error.URLError:
            logging.warning("Microlog: To view recordings, start the server: " \
                "uv run python src/microlog/server.py")

    def print_in_block(self, message: str) -> None:
        """Print a message in a decorative block."""
        sys.stdout.write(f"┏{'━' * (len(message) + 2)}┓\n")
        sys.stdout.write(f"┃ {message} ┃\n")
        sys.stdout.write(f"┗{'━' * (len(message) + 2)}┛\n")

    def get_application(self) -> str:
        """Get a short name for the current application/script."""
        if self.application:
            return self.application
        name = sys.argv[0]
        if name == "-c":
            name = "python"
        if name == "-m":
            name = sys.argv[1]
        name = "-".join(name.split("/")[-3:])
        name = name.replace("python-site-packages-", "").replace(".py", "")
        name = name.replace("python3 -m ", "")
        name = name.replace("python -m ", "")
        return name

    def get_identifier(self) -> str:
        """Generate a unique identifier for the recording."""
        date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        return f"{self.get_application()}/{date}"

    def get_log_path(self, identifier: str) -> str:
        """Get the file path for storing the recording."""
        path = os.path.join(config.S3_ROOT, identifier.replace(" ", "_"))
        return f"{path}.zip"

    def save(self) -> None:
        """Save the recording to a compressed file and notify the server."""
        # local import because pyscript only supports pure python modules
        import zstd  # pylint: disable=import-outside-toplevel

        identifier = self.get_identifier()
        pickled_data = pickle.dumps(self)
        compressed_data = zstd.compress(pickled_data) # pylint: disable=c-extension-no-member
        path = self.get_log_path(identifier)

        config.fs.makedir(os.path.dirname(path), exist_ok=True)
        with config.fs.open(path, "wb") as file:
            cast(Any, file).write(compressed_data)

        self.notify_server(identifier)
        self.show_details(identifier)

    def clear(self) -> None:
        """Clear the recording."""
        self.calls = []
        self.markers =[]
        self.statuses = []

    def load(self, pickled_data: bytes) -> None:
        """Load a recording from pickled data."""
        download = pickle.loads(pickled_data)
        self.calls = download.calls
        self.markers = download.markers
        self.statuses = download.statuses

    def add_status(
        self,
        when: float,
        cpu: float,
        system_cpu: float,
        memory: int,
        memory_total: int,
        memory_free: int,
        module_count: int,
        object_count: int,
    ) -> None:
        """Add a status update to the recording."""
        status = Status(
            when,
            cpu,
            system_cpu,
            memory,
            memory_total,
            memory_free,
            module_count,
            object_count,
        )
        if self.statuses and status.is_similar(self.statuses[-1]):
            return
        self.statuses.append(status)

    def add_call(
        self,
        when: float,
        thread_id: int,
        call_site: 'CallSite',
        caller_site: 'CallSite',
        depth: int,
        duration: float = 0.0,
    ) -> None:
        """Add a function/method call to the recording."""
        call = Call(when, thread_id, call_site, caller_site, depth, duration)
        self.calls.append(call)

    def add_marker(
        self,
        kind: int,
        when: float,
        message: str,
        stack: 'Stack',
        duration: float = 0.1,
    ) -> None:
        """Add a marker/event to the recording."""
        marker = Marker(kind, when, internalize(message), stack, duration)
        self.markers.append(marker)

class Model:
    """
    Base class for all models used in Microlog tracer, server, and UI.
    Enables code sharing between backend and UI for serialization.
    """

class Call(Model):
    """
    A Call represents a function/method call, with a CallSite representing 
    the location of the call.
    """
    def __init__(
        self,
        when: float,
        thread_id: int,
        call_site: 'CallSite',
        caller_site: 'CallSite',
        depth: int,
        duration: float = 0.0,
    ) -> None:
        """Initialize a Call instance."""
        self.when: float = round(when, 3)
        self.thread_id: int = thread_id
        self.call_site: CallSite = call_site
        self.caller_site: CallSite = caller_site
        self.depth: int = depth
        self.duration: float = round(duration, 3)

    def is_similar(self, other: 'Call' | None) -> bool:
        """Check if this call is similar to another call based on the call site."""
        return other is not None and self.call_site.is_similar(other.call_site)

    def __eq__(self, other: object) -> bool:
        """Check equality with another Call object."""
        return (
            isinstance(other, Call)
            and self.call_site == other.call_site
            and self.caller_site == other.caller_site
        )

    def __hash__(self) -> int:
        """Return the hash of the Call object."""
        return hash((self.call_site, self.caller_site))

    def __repr__(self) -> str:
        """Return a string representation of the Call object."""
        return f"<Call {self.call_site.name}@{self.call_site.lineno}>"

class CallSite:
    """A CallSite is a specific location where a function/method is defined."""
    def __init__(self, filename: str, lineno: int, name: str, when: float=0.0) -> None:
        """Initialize a CallSite instance."""
        self.filename: str = internalize(absolute_path(filename))
        self.lineno: int = lineno or 0
        self.name: str = internalize(name)
        self.when: float = when
        self.duration: float = 0.0

    def is_similar(self, other: 'CallSite' | None) -> bool:
        """Check if this CallSite is similar to another CallSite."""
        return (
            other is not None
            and self.filename == other.filename
            and self.lineno == other.lineno
            and self.name == other.name
        )

    def __eq__(self, other: object) -> bool:
        """Check equality with another CallSite object."""
        return isinstance(other, CallSite) and self.name == other.name

    def __hash__(self) -> int:
        """Return the hash of the CallSite object."""
        return hash(str(self))

    def __repr__(self) -> str:
        """Return a string representation of the CallSite object."""
        return f"<CallSite {self.filename}:{self.name}:{self.lineno}>"

CALLSITE_UNKNOWN: CallSite = CallSite("", 0, "UNKNOWN")
CALLSITE_IGNORE: CallSite = CallSite("", 0, "IGNORE")

class Stack:
    """
    A Stack represents a call stack at a specific point in time.
    Used during tracing to capture the current call stack for a thread.
    """
    def __init__(
        self,
        when: float = 0.0,
        start_frame: Any | None = None,
        index: int = 0,
        call_sites: list['CallSite'] | None = None,
    ) -> None:
        """Initialize a Stack instance."""
        self.index: int = index
        self.when: float = when
        self.call_sites: list[CallSite] = call_sites or []
        if start_frame:
            for frame, lineno in self.walk_stack(start_frame):
                call_site: CallSite = self.call_site_from_frame(frame, lineno)
                if call_site is CALLSITE_IGNORE:
                    continue
                self.call_sites.append(call_site)

    def walk_stack(self, start_frame: Any) -> list[tuple[Any, int]]:
        """Walk the stack frames starting from start_frame."""
        return [
            (frame, lineno)
            for frame, lineno in reversed(list(traceback.walk_stack(start_frame)))
        ]

    def call_site_from_frame(self, frame: Any, lineno: int) -> CallSite:
        """Create a CallSite from a frame and line number."""
        filename = frame.f_globals.get("__file__", "")
        name = frame.f_code.co_name
        module = frame.f_globals.get("__name__", "")
        if module == "__main__":
            module = filename.replace(".py", "").replace("\\", ".").replace("/", ".")
        instance = frame.f_locals["self"] if "self" in frame.f_locals else None
        clazz = ""
        if instance is not None:
            try:
                module = instance.__module__
                clazz = instance.__class__.__name__
            except Exception: # pylint: disable=broad-exception-caught
                module = clazz = str(instance.__class__)

        if module in config.IGNORE_MODULES or ".microlog." in module:
            return CALLSITE_IGNORE

        if name == "inner" and "func" in frame.f_locals:
            function = frame.f_locals["func"]
            name = function.__name__
            module = function.__module__
            clazz = inspect.getmro(function.__class__)[0].__name__

        name = f"{module}.{clazz}.{name}"
        if name == "..<module>":
            name = "python.builtin.exec"
        return CallSite(filename, lineno, name, self.when)

    def __iter__(self) -> Any:
        """Return an iterator over call_sites."""
        return iter(self.call_sites)

    def __len__(self) -> int:
        """Return the number of call_sites."""
        return len(self.call_sites)

    @overload
    def __getitem__(self, index: int) -> CallSite: ...
    @overload
    def __getitem__(self, index: slice) -> list[CallSite]: ...

    def __getitem__(self, index: int | slice) -> CallSite | list[CallSite]:
        """Return call_sites at the given index or slice."""
        return self.call_sites[index]

    def __repr__(self) -> str:
        """Return a string representation of the Stack object."""
        call_sites = " ".join(call_site.name for call_site in self.call_sites)
        return f"<Stack {self.index} {call_sites}\n>"

class Marker(Model):
    """
    A Marker represents an event or span in the recording, with an
    associated message and stack trace.
    """
    def __init__(
        self, kind: int, when: float, message: str, stack: Stack, duration: float = 0.1
    ) -> None:
        """Initialize a Marker instance."""
        self.when: float = round(when, 3)
        self.kind: int = kind
        self.message: str = message
        self.stack: Stack = stack
        self.duration: float = duration

class Status:
    """A Status represents the state of the system at a specific point in time."""
    def __init__(
        self,
        when: float,
        cpu: float,
        system_cpu: float,
        memory: int,
        memory_total: int,
        memory_free: int,
        module_count: int,
        object_count: int,
    ) -> None:
        """Initialize a Status instance."""
        self.when: float = round(when, 3)
        self.cpu: float = round(cpu)
        self.system_cpu: float = system_cpu
        self.memory: int = memory
        self.memory_total: int = memory_total
        self.memory_free: int = memory_free
        self.module_count: int = module_count
        self.object_count: int = object_count
        self.duration: float = 0.0

    def is_similar(self, other: 'Status') -> bool:
        """Check if this Status is similar to another Status."""
        return (
            other is not None
            and self.cpu == other.cpu
            and self.memory == other.memory
            and self.memory_total == other.memory_total
            and self.memory_free == other.memory_free
            and self.module_count == other.module_count
            and self.object_count == other.object_count
        )

def to_gb(amount: int) -> str:
    """Convert a byte amount to a human-readable string in GB, MB, KB, or bytes."""
    if amount / GB > 1:
        return f"{amount / GB:.1f}GB"
    if amount / MB > 1:
        return f"{amount / MB:.1f}MB"
    if amount / KB > 1:
        return f"{amount / KB:.1f}KB"
    return f"{amount} bytes"

recording = Recording()
