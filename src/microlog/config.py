#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Configuration module for Microlog."""

import os
from pathlib import Path
import re


EVENT_KIND_CALL = 1
EVENT_KIND_STATUS = 2
EVENT_KIND_INFO = 3
EVENT_KIND_WARN = 4
EVENT_KIND_DEBUG = 5
EVENT_KIND_ERROR = 6
EVENT_KIND_CALLSITE = 7
EVENT_KIND_MARKER = 8
EVENT_KIND_STACK = 9
EVENT_KIND_SYMBOL = 10
EVENT_KIND_CUSTOM = 15

KB = 1024
MB = KB * KB
GB = MB * KB

BUILTIN_MODULES = {
    "__future__",
    "_abc",
    "_collections",
    "_distutils_hack",
    "_frozen_importlib",
    "_frozen_importlib_external",
    "_io",
    "_json",
    "_sitebuiltins",
    "_thread",
    "_weakrefset",
    "ast",
    "builtins",
    "calendar",
    "collections",
    "email._policybase",
    "email.charset",
    "encodings.utf_8",
    "functools",
    "http",
    "itertools",
    "json.decoder",
    "json.encoder",
    "logging",
    "microlog",
    "microlog.api",
    "microlog.log",
    "microlog.models",
    "microlog.server",
    "microlog.tracer",
    "operator",
    "os",
    "pathlib",
    "psutil",
    "psutil._common",
    "random",
    "re",
    "reprlib",
    "socketserver",
    "string",
    "threading",
    "traceback",
    "types",
    "typing",
    "weakref",
}

BASIC_TYPES = (
    Exception,
    list,
    dict,
    tuple,
    set,
    str,
    int,
    float,
    bool,
    type(None),
)

TRACER_STATUS_DELAY = float(os.environ.get("MICROLOG_STATUS_DELAY", 0.1))
TRACER_MEMORY_DELAY = float(os.environ.get("MICROLOG_MEMORY_DELAY", 1.0))
TRACER_SAMPLE_DELAY = float(os.environ.get("MICROLOG_SAMPLE_DELAY", 0.05))

IGNORE_MODULES = [
    "runpy",
    "threading",
    "microlog",
    "microlog.api",
    "microlog.tracer",
    "microlog.__main__",
    "importlib._bootstrap",
    "_frozen_importlib_external",
]

HOST = "0.0.0.0"
PORT = 7777

class LocalFileSystem:
    """A simple local filesystem interface to mimic s3fs methods used in microlog."""
    def walk(self, root: str):
        """Generate the file names in a directory tree by walking the tree."""
        for dirpath, dirnames, filenames in os.walk(root):
            yield dirpath, dirnames, filenames

    def makedir(self, path: str, exist_ok: bool = True) -> None:
        """Create a directory and any necessary parent directories."""
        os.makedirs(path, exist_ok=exist_ok)

    def ls(self, path: str) -> list[str]:
        """List the contents of a directory."""
        return os.listdir(path)

    def open(self, path: str, mode: str = "r"):
        """Open a file."""
        return open(path, mode, encoding="utf-8" if "b" not in mode else None)

    def rm(self, path: str) -> None:
        """Remove a file."""
        os.remove(path)

try:
    import s3fs # local import because pyscript only supports pure python modules
    S3_ROOT = os.environ["MICROLOG_S3_ROOT"]
    S3_ARGS = {
        "region": os.environ["MICROLOG_S3_REGION"]
    }
    fs = s3fs.S3FileSystem(
        anon=False,
        config_kwargs=S3_ARGS,
        client_kwargs=S3_ARGS,
        use_listings_cache=False,
    )
    fs.exists(S3_ROOT)  # Test if credentials are valid
    SERVER = os.environ["MICROLOG_SERVER"]
except Exception: # pylint: disable=broad-except
    S3_ROOT = os.path.expanduser("~/microlog")
    SERVER = "http://localhost:7777/"
    fs = LocalFileSystem()

fs.makedir(S3_ROOT, exist_ok=True)


try:
    if version_match := re.search(
        pattern=r'version = "([^"]+)"',
        string=(Path(__file__).parents[2] / "pyproject.toml").read_text(),
    ):
        version = version_match.group(1)
except FileNotFoundError:
    version = "unknown" # pylint: disable=invalid-name
