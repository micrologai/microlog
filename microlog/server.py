#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import appdata
import json
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
verbose = True

class LogServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if verbose: print("GET", self.path)
        try:
            if self.path == "/logs":
                logs = []
                for root, dirs, files in os.walk(paths.logs_path, topdown=False):
                    for name in sorted([file for file in files if file.endswith(".zip")]):
                        application, version = root.split("/")[-2:]
                        if name.endswith(".zip"):
                            logs.append(f"{application}/{version}/{name[:-4]}\n")
                return self.sendData("text/html", bytes("\n".join(logs), encoding="utf-8"))

            if self.path.startswith("/zip/"):
                name = f"{self.path[5:]}.log.zip"
                path = os.path.join(paths.logs_path, name)
                compressed = open(path, "rb").read()
                log = zlib.decompress(compressed)
                return self.sendData("text/html", log)

            if self.path.startswith("/delete/"):
                name = f"{self.path[8:]}.log.zip"
                path = os.path.join(paths.logs_path, name)
                os.remove(path)
                return self.sendData("text/html", bytes("OK", encoding="utf-8"))

            if self.path in ["/stop"]:
                return 

            if self.path.startswith("/images/"):
                return self.sendData("image/png", open(self.path[1:], "rb").read())

            if self.path in ["", "/"] or self.path.startswith("/log/") and not self.path.endswith(".py"):
                return self.sendData("text/html", bytes(f"{open('dashboard/index.html').read()}", encoding="utf-8"))

            name = "/".join(self.path.split("/")[4:]) if self.path.startswith("/log/") else self.path[1:]
            return self.sendData("text/html", bytes(f"{open(name).read()}", encoding="utf-8"))
        except Exception as e:
            print(e)
            return ""

        
    def sendData(self, kind, data):
        self.send_response(200)
        self.send_header("Content-type", kind)
        self.send_header("Access-Control-Allow-Origin", f"http://{hostName}:{dashboardServerPort}")
        self.end_headers()
        self.wfile.write(data)
        print(" - sent", len(data), "bytes")

    def log_message(self, format, *args):
        return


class Server():
    running = False

    def start(self):
        self.running = True
        try:
            self.server = HTTPServer((hostName, serverPort), LogServer)
            if verbose:
                print(f"microlog.server: local log server started - will autostop after {autostopDelay} seconds.")
                print(f"microlog.server: logs path: {paths.logs_path}")
            while self.running:
                self.server.handle_request()
            if verbose: print("microlog.server: local log server stopped")
        except Exception as e:
            print(f"microlog.server:", e)

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
