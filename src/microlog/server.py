#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Microlog server module."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import logging
import os
import re
import subprocess
import sys
import time
import traceback
from typing import Any
from typing import cast
from typing import Union
import urllib.parse

from microlog import config
from microlog import analyse


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)


def info(message: str) -> None:
    """Log an info message."""
    logging.info(message)


def error(message: str) -> None:
    """Log an error message."""
    logging.error(message)


class LogWatcher:
    """Watches and manages the list of available log recordings."""
    logs: list[str] = []

    def __init__(self) -> None:
        """Initialize LogWatcher and load logs."""
        self.load_logs()

    def get_recording_names(self) -> list[str]:
        """Return the list of recording names."""
        return self.logs

    def rm(self, name: str) -> None:
        """Remove a log from the list by name."""
        self.logs = list(set(self.logs) - {name})
        info(f"Remove log: {name} => {len(self.logs)} logs")

    def save(self, name: str) -> None:
        """Add a log to the list by name."""
        self.logs = list(set(self.logs + [name]))
        info(f"Add log: {name} => {len(self.logs)} logs")

    def load_logs(self) -> None:
        """Load logs from the configured S3 root."""
        info(f"Loading logs from {config.fs.__class__.__name__}...")
        start = time.time()
        logs = []
        try:
            for root, _, files in config.fs.walk(config.S3_ROOT):
                application = str(root).rsplit("/", 1)[-1] \
                            .replace("\\", "/") \
                            .replace("microlog/", "")
                for name in sorted([file for file in files if file.endswith(".zip")]):
                    if not "/" in application:
                        logs.append(f"{application}/{name[:-4]}")
        except AttributeError:
            # Happens when no S3 credentials are configured
            pass
        end = time.time()
        info(f"Found {len(logs)} recordings in {end - start:.1f}s")
        self.logs = logs


log_watcher: LogWatcher = LogWatcher()


class LogServerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Microlog server."""

    def do_POST(self) -> None: # pylint: disable=invalid-name
        """Handle POST requests."""
        if "/analysis/" in self.path:
            content_length = int(self.headers['Content-Length'])
            post_data_bytes = self.rfile.read(content_length)
            data = post_data_bytes.decode("utf-8")
            try:
                self.analyse(data)
            except Exception as e:  # pylint: disable=broad-except
                error(str(e))
                traceback.print_exc()
                name = data.split("\n", 1)[0]
                self.send_data(
                    "text/html",
                    bytes(f"{name}\nError: {e}", encoding="utf-8"),
                )

    def do_GET(self) -> None: # pylint: disable=invalid-name
        """Handle GET requests."""
        try:
            if ".well-known/appspecific/com.chrome.devtools.json" in self.path:
                return
            elif "/logs?" in self.path:
                self.get_recording_names()
            elif "/zip/" in self.path:
                self.get_recording()
            elif self.path.startswith("/delete/"):
                self.delete_log()
            elif self.path.startswith("/save/"):
                self.save_log()
            elif self.path in ["", "/"]:
                self.get_index()
            elif self.path.startswith("images/") or "/images/" in self.path:
                self.get_image()
            else:
                self.get_resource()
        except Exception as e:  # pylint: disable=broad-except
            error(str(e))
            traceback.print_exc()
            self.send_data(
                "text/html",
                bytes(f"Error: {e}", encoding="utf-8"),
            )

    def get_full_path(self, path: str) -> str:
        """Return the full filesystem path for a given resource path."""
        path = path.replace("/microlog//", "")
        path = path.replace("/microlog/microlog/", "/microlog/")
        full_path = path[1:] if path.startswith("/") else path
        if not os.path.exists(full_path):
            full_path = full_path.replace("src/microlog/", "")
        if not os.path.exists(full_path):
            full_path = os.path.join(os.path.dirname(__file__), full_path)
        return full_path

    def get_resource(self) -> None:
        """Serve a static resource file."""
        path = self.get_full_path(self.path)
        try:
            with open(path, encoding="utf-8") as fd:
                return self.send_data(
                    "text/html",
                    bytes(f"{fd.read()}", encoding="utf-8"),
                    {"Cache-Control": "public, max-age=86400"},
                )
        except Exception as e:  # pylint: disable=broad-except
            error_msg = f"Error - Resource not found: {path}: {e}"
            logging.error(error_msg)
            return self.send_data(
                "text/html",
                bytes(f"Cannot open {self.path} {path}: {e}", encoding="utf-8"),
            )

    def get_index(self) -> None:
        """Serve the main dashboard index HTML page."""
        path = self.get_full_path("src/microlog/index.html")
        try:
            with open(path, encoding="utf-8") as fd:
                html = fd.read()
            html = (
                html.replace("{microlog_version}", config.version)
                .replace("{microlog_repo_owner}", "micrologai")
                .replace("{microlog_repo_name}", "microlog")
            )
            return self.send_data("text/html", bytes(f"{html}", encoding="utf-8"))
        except FileNotFoundError:
            error_msg = f"Error - File not found: {self.path} {path}"
            logging.error(error_msg)
            return self.send_data(
                "text/html",
                bytes(f"Cannot open {self.path} {path}", encoding="utf-8"),
            )

    def get_image(self) -> None:
        """Serve an image file."""
        path = self.get_full_path(self.path)
        with open(path, "rb") as fd:
            return self.send_data("image/png", fd.read())

    def analyse(self, prompt) -> None:
        """Serve an analysis of the recording using an LLM."""
        return self.send_data(
            "text/html",
            bytes(analyse.analyse_recording(prompt), encoding="utf-8"),
        )

    def get_recording_names(self) -> None:
        """Serve the list of available recording names, filtered by query."""
        start = time.time()
        query = urllib.parse.urlparse(self.path).query
        query_components = dict(qc.split("=") for qc in query.split("&"))
        name_filter = re.compile(query_components["filter"].lower())
        logs = [
            log
            for log in log_watcher.get_recording_names()
            if re.search(name_filter, log.lower()) is not None
        ]
        end = time.time()
        info(f"Returning {len(logs):,d} recordings in {end - start:.1f}s")
        return self.send_data("text/html", bytes("\n".join(logs), encoding="utf-8"))

    def load_recording(self) -> Union[str, bytes]:
        """Load a compressed recording file."""
        name = self.path[self.path[1:].index("/")+2:]
        path = os.path.join(config.S3_ROOT, f"{name}.zip")
        if not os.path.exists(path):
            path = os.path.join(config.S3_ROOT, f"{name}.log.zip")
        compressed_bytes: bytes = b""
        with config.fs.open(path, "rb") as fd:
            compressed_bytes = cast(Any, fd.read())
        return name, compressed_bytes

    def get_recording(self) -> None:
        """Serve a compressed recording file."""
        name, recording = self.load_recording()
        info(f"Send recording {name}: ({len(recording):,d} bytes)")
        return self.send_data(
            "application/microlog",
            recording,
            {"Cache-Control": "public, max-age=86400", "Content-Encoding": "zstd"},
        )

    def parse_path(self) -> tuple[str, str]:
        """Parse the log name and path from the request path."""
        slash_index = self.path.index("/", 1)
        name = f"{self.path[slash_index + 1 :]}".replace("%20", " ")
        path = os.path.join(config.S3_ROOT, f"{name}.zip")
        if not os.path.exists(path):
            path = os.path.join(config.S3_ROOT, f"{name}.log.zip")
        return name, path

    def delete_log(self) -> Any:
        """Delete a log file and remove it from the watcher."""
        name, path = self.parse_path()
        log_watcher.rm(name)
        if config.fs:
            config.fs.rm(path)
        return self.send_data("text/html", bytes("OK", encoding="utf-8"))

    def save_log(self) -> Any:
        """Save a log file and add it to the watcher."""
        name, _ = self.parse_path()
        log_watcher.save(name)
        return self.send_data("text/html", bytes("OK", encoding="utf-8"))

    def send_data(
        self, kind: str, data: bytes, headers: dict[str, str] | None = None
    ) -> None:
        """Send HTTP response data with headers."""
        self.send_response(200)
        self.send_header("Content-type", kind)
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)


class Server:
    """Microlog HTTP server runner."""
    def start(self) -> None:
        """Start the Microlog HTTP server."""
        try:
            info(f"Starting Microlog server... http://{config.HOST}:{config.PORT}")
            HTTPServer((config.HOST, config.PORT), LogServerHandler).serve_forever()
        except OSError:
            pass


def run() -> None:
    """Run the Microlog server as a subprocess."""
    subprocess.Popen([sys.executable, __file__])


if __name__ == "__main__":
    Server().start()
