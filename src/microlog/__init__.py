#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Microlog package initialization."""

from .api import enabled
from .api import start
from .api import stop
from .api import is_running
from .api import print # pylint: disable=redefined-builtin


__all__ = [
    "is_running",
    "enabled",
    "start",
    "stop",
    "print",
]


def main() -> None:
    """Entry point for command-line usage."""
    from microlog.__main__ import main as cli_main # pylint: disable=import-outside-toplevel

    cli_main()
