#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import appdata
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import os
import threading
import time
import urllib.request
import zlib

hostName = "127.0.0.1"
dashboardServerPort = 3000
serverPort = 4000
paths = appdata.AppDataPaths('microlog')
autostopDelay = 600

class LogServer(BaseHTTPRequestHandler):
    files = [
        "dashboard/main.py",
        "dashboard/__init__.py",
        "dashboard/canvas.py",
        "dashboard/colors.py",
        "dashboard/dialog.py",
        "dashboard/views/__init__.py",
        "dashboard/views/call.py",
        "dashboard/views/config.py",
        "dashboard/views/marker.py",
        "dashboard/views/span.py",
        "dashboard/views/status.py",
        "dashboard/views/timeline.py",
        "microlog/config.py",
        "microlog/events.py",
        "microlog/memory.py",
        "microlog/marker.py",
        "microlog/profiler.py",
        "microlog/settings.py",
        "microlog/span.py",
        "microlog/stack.py",
        "microlog/threads/__init__.py",
        "microlog/threads/status.py",
        "microlog/symbols.py",
    ]

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Access-Control-Allow-Origin", f"http://{hostName}:{dashboardServerPort}")
        self.end_headers()

        if self.path == "/logs":
            for root, dirs, files in os.walk(paths.logs_path, topdown=False):
                for name in sorted([file for file in files if file.endswith(".zip")]):
                    application, version = root.split("/")[-2:]
                    if name.endswith(".zip"):
                        self.wfile.write(bytes(f"{application}/{version}/{name[:-4]}\n", encoding="utf-8"))
            return

        if self.path.startswith("/zip/"):
            name = f"{self.path[5:]}.log.zip"
            path = os.path.join(paths.logs_path, name)
            compressed = open(path, "rb").read()
            log = zlib.decompress(compressed)
            return self.wfile.write(log)

        if self.path in ["/favicon.ico", "/stop"]:
            return 

        if self.path in ["", "/"] or self.path.startswith("/log/") and not self.path.endswith(".py"):
            return self.wfile.write(bytes(f"{open('dashboard/index.html').read()}", encoding="utf-8"))

        name = "/".join(self.path.split("/")[4:]) if self.path.startswith("/log/") else self.path[1:]
        if name in self.files:
            return self.wfile.write(bytes(f"{open(name).read()}", encoding="utf-8"))
        else:
            print("Not a known file:", name, self.path)

        print("microlog.server: ERROR", self.path)


    def log_message(self, format, *args):
        return


class Server():
    running = False

    def start(self):
        self.running = True
        try:
            self.server = HTTPServer((hostName, serverPort), LogServer)
            print(f"microlog.server: local log server started - will autostop after {autostopDelay} seconds.")
            while self.running:
                self.server.handle_request()
            print("microlog.server: local log server stopped")
        except:
            pass

    def stop(self):
        self.running = False
        try:
            # force one more event to stop the server loop
            urllib.request.urlopen(f"http://{hostName}:{serverPort}/stop")
        except:
            pass # server already shut down

server = Server()


def start():
    def autostop():
        time.sleep(autostopDelay)
        stop()

    threading.Thread(target=autostop).start()
    server.start()


def stop():
    server.stop()


if __name__ == "__main__":
    server.start()
