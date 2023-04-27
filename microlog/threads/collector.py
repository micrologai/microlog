#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import appdata
import datetime
import json
import os
import time
import zlib

from microlog import events
from microlog import config
from microlog import settings
from microlog import threads

FLUSH_INTERVAL_SECONDS = 10.0

paths = appdata.AppDataPaths('microlog')
if paths.require_setup:
    paths.setup()

class FileCollector(threads.BackgroundThread):
    done = False
    lastFlush = 0

    def start(self) -> None:
        self.daemon = True
        self.fd, self.path = self.getFile()
        self.buffer = []
        self.url = "http://127.0.0.1:4000/"
        self.delay = 0
        return threads.BackgroundThread.start(self)

    
    def sanitize(self, filename):
        return filename.replace("/", "_")

    def getIdentifier(self):
        application = settings.current.application
        version = settings.current.version
        date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        return f"{self.sanitize(application)}/{self.sanitize(str(version))}/{date}"

    def getFile(self):
        self.identifier = self.getIdentifier()
        path = paths.get_log_file_path(self.identifier)
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)
        return os.open(path, os.O_RDWR|os.O_CREAT), path

    def reopen(self):
        self.flush()
        os.close(self.fd)
        oldPath = self.path
        oldLog = open(oldPath).read()
        self.fd, self.path = self.getFile()
        os.write(self.fd, str.encode(oldLog))
        os.truncate(oldPath, 0)
        os.remove(oldPath)

    def run(self) -> None:
        while True:
            event = events.get()
            self.profiler.enable()
            self.handleEvent(event)
            self.profiler.disable()
            if self.delay:
                time.sleep(self.delay)
    
    def getEvent(self):
        self.handleEvent(events.get())

    def handleEvent(self, event):
        line = f'{",".join(json.dumps(e) for e in event)}\n'
        self.buffer.append(line)
        config.totalLogEventCount += 1
        self.flush()

    def flush(self, force=False):
        if force or time.time() - self.lastFlush > FLUSH_INTERVAL_SECONDS:
            self.lastFlush = time.time()
            try:
                os.write(self.fd, str.encode("".join(self.buffer)))
            except Exception as e:
                pass # file was already closed
            self.buffer.clear()

    def compress(self):
        path = f"{self.path}.zip"
        with open(path, "wb") as fd:
            uncompressed = open(self.path, "rb").read()
            compressed = zlib.compress(uncompressed, level=9)
            fd.write(compressed)
        return path

    def stop(self):
        if self.done:
            return
        self.done = True
        while not events.empty():
            self.getEvent()
        self.flush(force=True)
        os.close(self.fd)
        config.outputFilename = self.path
        config.zipFilename = self.zip = self.compress()
        config.outputUrl = self.url = f"http://127.0.0.1:4000/log/{self.identifier}"