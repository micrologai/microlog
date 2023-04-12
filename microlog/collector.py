#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import appdata
import datetime
import json
import os
import threading
import time
import zlib

from microlog import events
from microlog import config
from microlog import settings
from microlog.config import micrologBackgroundService

FLUSH_INTERVAL_SECONDS = 10.0

paths = appdata.AppDataPaths('microlog')
if paths.require_setup:
    paths.setup()

class FileCollector(threading.Thread):
    done = False
    lastFlush = 0

    def start(self) -> None:
        self.setDaemon(True)
        self.fd, self.path = self.getFile()
        self.buffer = []
        self.url = "http://127.0.0.1:4000/"
        return super().start()
    
    def getFile(self):
        application = settings.current.application
        version = settings.current.version
        date = datetime.datetime.now().strftime("%d-%b-%Y-%H:%M:%S")
        path = paths.get_log_file_path(name=f"{application}-{version}-{date}")
        return os.open(path, os.O_RDWR|os.O_CREAT), path

    def run(self) -> None:
        while True:
            self.getEvent()

    def getEvent(self):
        self.handleEvent(events.get())

    @micrologBackgroundService("FileCollector")
    def handleEvent(self, event):
        line = f'{",".join(json.dumps(e) for e in event)}\n'
        self.buffer.append(line)
        config.totalLogEventCount += 1
        self.flush()

    @micrologBackgroundService("FileCollector")
    def flush(self, force=False):
        if force or time.time() - self.lastFlush > FLUSH_INTERVAL_SECONDS:
            self.lastFlush = time.time()
            try:
                os.write(self.fd, str.encode("".join(self.buffer)))
            except Exception as e:
                print(e)
            self.buffer.clear()

    def compress(self):
        path = f"{self.path}.zip"
        with open(path, "wb") as fd:
            uncompressed = open(self.path, "rb").read()
            compressed = zlib.compress(uncompressed, level=9)
            fd.write(compressed)
        return path


    def stop(self):
        self.done = True
        while not events.empty():
            self.getEvent()
        self.flush(force=True)
        os.close(self.fd)
        config.outputFilename = self.path
        config.zipFilename = self.zip = self.compress()
        config.outputUrl = self.url = f"http://127.0.0.1:4000/log/{os.path.basename(self.zip)}"