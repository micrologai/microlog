#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import appdata
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import json
import logging
import os
import psutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import bz2

hostName = "127.0.0.1"
dashboardServerPort = 3000
serverPort = 4000
paths = appdata.AppDataPaths('microlog')
autostopDelay = 600
logger = logging.Logger("Microlog.server")
logging.basicConfig()
logger.level=logging.INFO


def debug(s):
    print(s)
    logger.info(s)


class LogServer(BaseHTTPRequestHandler):
    def do_GET(self):
        debug(f"GET {self.path}")
        try:
            if self.path.startswith("/logs?"):
                import urllib
                query = urllib.parse.urlparse(self.path).query
                query_components = dict(qc.split("=") for qc in query.split("&"))
                filter = query_components["filter"]
                logs = []
                for root, dirs, files in os.walk(paths.logs_path, topdown=False):
                    for name in sorted([file for file in files if file.endswith(".zip")]):
                        application = root.split("/")[-1]
                        if name.endswith(".zip") and filter in root:
                            logs.append(f"{application}/{name[:-4]}\n")
                return self.sendData("text/html", bytes("\n".join(logs), encoding="utf-8"))

            if self.path.startswith("/zip/"):
                name = f"{self.path[5:]}.log.zip".replace("%20", " ")
                return self.sendData("application/microlog", self.readLog(name))

            if self.path.startswith("/delete/"):
                name = f"{self.path[8:]}.log.zip".replace("%20", " ")
                if name.startswith("logs/"):
                    name = name[5:]
                path = os.path.join(paths.logs_path, name)
                os.remove(path)
                return self.sendData("text/html", bytes("OK", encoding="utf-8"))

            if self.path.startswith("/explain/"):
                import explain
                name = f"{self.path[9:]}.log.zip".replace("%20", " ")
                log = self.readLog(name)
                debug(f"Explain {name}")
                debug(f"Log is {len(log)} bytes")
                explanation = explain.explainLog(name.split("/")[0], log.decode("utf-8"))
                print(explanation)
                return self.sendData("text/html", bytes(explanation, encoding="utf-8"))

            if self.path in ["/stop"]:
                return 

            if self.path.startswith("/images/"):
                with open(f"microlog/{self.path[1:]}", "rb") as fd:
                    return self.sendData("image/png", fd.read())

            if self.path in ["", "/"] or self.path.startswith("/?filter=") or self.path.startswith("/log/") and not self.path.endswith(".py"):
                with open('dashboard/index.html') as fd:
                    return self.sendData("text/html", bytes(f"{fd.read()}", encoding="utf-8"))

            name = "/".join(self.path.split("/")[4:]) if self.path.startswith("/log/") else self.path[1:]
            with open(name) as fd:
                return self.sendData("text/html", bytes(f"{fd.read()}", encoding="utf-8"))
        except Exception as e:
            logging.error(e)
            import traceback
            traceback.print_exc()
            return str(e)

    def readLog(self, name):
        if name.startswith("logs/"):
            name = name[5:]
        path = os.path.join(paths.logs_path, name)
        with open(path, "rb") as fd:
            compressed = fd.read()
        return bz2.decompress(compressed)
        
    def sendData(self, kind, data):
        self.send_response(200)
        self.send_header("Content-type", kind)
        self.send_header("Access-Control-Allow-Origin", f"http://{hostName}:{dashboardServerPort}")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


class Server():
    running = False

    def start(self):
        self.running = True
        try:
            try:
                self.startServer()
            except OSError as e: # server is already running
                try:
                    self.killServer()
                    self.startServer()
                except OSError as e: # server is already running
                    raise 
        except Exception as e:
            logging.error(e)
        
    def killServer(self):
        debug("Server already running. Find it and stop it.")
        for pid in psutil.pids():
            try:
                cmd = " ".join(psutil.Process(pid).cmdline())
                if "/microlog/server.py" in cmd:
                    debug(f"Found server process {pid}: {cmd}")
                    os.kill(pid, signal.SIGABRT)
                    debug("Stopped existing server")
                    for n in range(1, 4):
                        debug("." * n)
                        time.sleep(1)
            except Exception as e:
                pass
    
    def startServer(self):
        self.server = HTTPServer((hostName, serverPort), LogServer)
        debug(f"Local log server started - will autostop after {autostopDelay} seconds.")
        debug(f"Logs path: {paths.logs_path}")
        while self.running:
            self.server.handle_request()
        debug("Local log server stopped")

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


def run():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((hostName, serverPort)) != 0:
            subprocess.Popen([sys.executable, __file__])

if __name__ == "__main__":
    debug(f"Starting server on port {serverPort}")
    server.start()
