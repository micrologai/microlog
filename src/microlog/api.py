#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""API module for Microlog."""

from __future__ import annotations

import inspect
import logging
import os
import re
import sys
import time
from typing import Any
import uuid

from microlog import config
from microlog import models


def log(kind: int, *args: Any, duration: float = 0.1) -> None:
    """Log an event of a given kind with a message constructed from args."""
    when = now()
    message = " ".join([str(arg) for arg in args])
    models.recording.add_marker(
        kind,
        when,
        message,
        models.Stack(
            when, inspect.currentframe()
        ),
        duration,
    )


def print(*args: Any) -> None: # pylint: disable=redefined-builtin
    """Log an info message to microlog"""
    log(config.EVENT_KIND_INFO, *args)

_begin: float = time.perf_counter() # Time when the program started


def now() -> float:
    """Get the current time in seconds since the start of the program."""
    return time.perf_counter() - _begin


class _Microlog:
    """Singleton class to manage Microlog state."""

    def __init__(self) -> None:
        """Initialize the Microlog instance."""
        self.running: bool = False
        self.tracer = None
        self.status = None

    def is_running(self) -> bool:
        """Check if Microlog is currently running."""
        return self.running

    def start(self, application: str = "") -> None:
        """Start Microlog logging for the application."""
        # delayed import to avoid circular dependency
        from microlog import tracer  # noqa: I001  pylint: disable=import-outside-toplevel

        if os.environ.get("MICROLOG_DISABLE", "false").lower() == "true":
            return  # Skip microlog
        if self.running:
            return  # Already running

        # Set up parent-child relationship of Microlog recordings
        os.environ["MICROLOG_PARENT_ID"] = parent_identifier = os.environ.get(
            "MICROLOG_ID", ""
        )
        os.environ["MICROLOG_ID"] = identifier = uuid.uuid4().hex

        log(config.EVENT_KIND_INFO, f"Microlog application: '{application}'")
        log(config.EVENT_KIND_INFO, f"Microlog Parent ID: '{parent_identifier}'")
        log(config.EVENT_KIND_INFO, f"Microlog ID: '{identifier}'")
        log(config.EVENT_KIND_INFO, f"Python version: {sys.version}")
        models.recording.application = application
        self.tracer = tracer.Tracer()
        self.status = tracer.StatusGenerator()
        self.log_environment()
        self.running = True

    def log_environment(self) -> None:
        """Log the current environment variables."""
        os.environ["MICROLOG_VERSION"] = config.version
        lines = [
            "## Command line",
            f"{sys.executable} {' '.join(sys.argv)}",
            "## Environment",
        ] + [f" - {key}: {value}" for key, value in get_safe_environment().items()]
        log(config.EVENT_KIND_DEBUG, "\n".join(lines))

    def stop_thread(self, thread: Any) -> None:
        """Stop a background thread gracefully."""
        try:
            thread.stop()
            if thread.is_alive():
                try:
                    thread.join()
                except RuntimeError:
                    # The thread was already stopped
                    pass
        except Exception as e: # pylint: disable=broad-except
            message = f"Microlog: Could not stop thread: {e}"
            logging.error(message)

    def stop(self) -> None:
        """Stop Microlog logging and save the recording."""
        if not self.running:
            return

        self.stop_thread(self.tracer)
        self.stop_thread(self.status)
        self.save_recording()

    def save_recording(self) -> None:
        """Save the current recording to persistent storage."""
        try:
            models.recording.save()
        except Exception as e: # pylint: disable=broad-except
            message = f"Microlog: Could not save the current recording: {e}"
            logging.error(message)
        finally:
            self.running = False


_singleton: _Microlog = _Microlog()

start = _singleton.start
is_running = _singleton.is_running
stop = _singleton.stop


class enabled: # pylint: disable=invalid-name
    """Context manager to enable Microlog logging within a block."""
    def __init__(self, *args: Any, **argv: Any) -> None:
        self.args: tuple[Any, ...] = args
        self.argv: dict[str, Any] = argv

    def __enter__(self) -> None:
        start(*self.args, **self.argv)
        return self

    def __exit__(self, *args: Any) -> None:
        stop()


SHELL_COLOR_YELLOW_BG: str = "\033[43m\033[0;30m"
SHELL_COLOR_RESET: str = "\033[0m"


RE_FIND_REPO: re.Pattern[str] = re.compile(r"^/home/coder/([^/]+)/.*")
RE_FIND_PATH: re.Pattern[str] = re.compile(r"^/home/coder/[^/]+/(.*)")


def short_file(filename: str) -> str:
    """Get the short file name from a full path."""
    parts = filename.split("/")
    if parts[-1] == "__init__.py":
        parts.pop()
    return parts[-1]


def create_link(filename: str, lineno: int, label: str | None = None) -> str:
    """Create a clickable VSCode source link for a file and line number."""
    path = re.sub(RE_FIND_PATH, r"\1", filename)
    label = label or f"{short_file(path)}:{lineno}"
    url = (
        f"vscode://file/{path}:{lineno}:1"
    )
    return f"<a href='{url}'>{label}</a>"


def is_sensitive_key(key: str) -> bool:
    """Determine if an environment variable contains sensitive information"""
    sensitive_keywords: list[str] = [
        "activation_code", "api_key", "apikey", "auth", "bearer", "cert",
        "askpass", "token", "cloud_key", "cloudkey",
        "logname", "username", "path", "user", "userid", "user_id",
        "home", "pythonstartup", "uv", "virtual_env", "virtualenv",
        "certificate", "connection_string", "cookie", "cred", "credential",
        "database_url", "dsn", "hash", "jwt", "key", "nonce", "oauth", "passwd",
        "password", "private", "pwd", "salt", "secret", "serial", "session",
        "signature", "token", "webhook",
    ]
    key_lower: str = key.lower()
    for keyword in sensitive_keywords:
        if keyword in key_lower:
            return True

    return False


def format_sensitive(key: str, value: str) -> str:
    """Enhanced sensitive formatting"""
    if is_sensitive_key(key):
        return "*" * len(value)
    return value


def get_safe_environment() -> dict[str, str]:
    """Get environment variables with sensitive values masked"""
    safe_env: dict[str, str] = {}

    for key, value in os.environ.items():
        safe_env[key] = format_sensitive(key, value)

    return safe_env
