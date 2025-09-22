"""
Microlog command-line interface.
"""

from __future__ import annotations

import logging
import os
import runpy
import sys
import traceback

import microlog


def usage(error) -> None:
    """Print usage information."""
    logging.error(error)
    logging.error("Usage: uv run -m microlog <label> <script> [script_args...]")
    logging.error("   or: uv run -m microlog <label> -m <module_name> [script_args...]")


def run(label: str, script_path: str, script_args: list[str]) -> None:
    """Run a script with microlog enabled."""

    # Set up environment
    original_argv = sys.argv
    script_dir = os.path.dirname(os.path.abspath(script_path))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        with microlog.enabled(label):
            if script_path == "-m":
                module_name = script_args[0]
                script_args = script_args[1:]
                sys.argv = [module_name] + script_args
                message = f"Microlog run module: {module_name} {script_args}"
                logging.info(message)
                runpy.run_module(module_name, run_name="__main__")
            else:
                sys.argv = [script_path] + script_args
                message = f"Microlog run module: {script_path} {script_args}"
                logging.info(message)
                runpy.run_path(script_path, run_name="__main__")
    except Exception as e: # pylint: disable=broad-except
        usage(f"Microlog Error: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        sys.argv = original_argv


def main() -> None:
    """Entry point for command-line usage."""
    if len(sys.argv) < 3:
        usage("Invalid arguments")
        sys.exit(1)
    label = sys.argv[1]  # Get the script label (e.g., 's267v2')
    script = sys.argv[2]  # Get script arguments
    args = sys.argv[3:]  # Get script arguments
    run(label, script, args)


if __name__ == "__main__":
    main()
