#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import atexit
import inspect
import os
import sys
import traceback

from microlog import config
from microlog import models

def info(*args):
    _log(config.EVENT_KIND_INFO, *args)


def warn(*args):
    _log(config.EVENT_KIND_WARN, *args)


def debug(*args):
    _log(config.EVENT_KIND_DEBUG, *args)


def error(*args):
    _log(config.EVENT_KIND_ERROR, *args)


def _log(kind, *args):
    from microlog import log
    from microlog import models
    when = log.log.now()
    message = " ".join([ str(arg) for arg in args ])
    stack = [
        f"{os.path.abspath(frame.filename)}#{frame.lineno}#{line[:-1]}"
        for frame, line in zip(reversed(inspect.stack()), traceback.format_stack())
        if not "microlog/tracer" in frame.filename and not "<frozen importlib" in frame.filename
    ]
    marker = models.Marker(kind, when, message, stack)
    log.log.addMarker(marker)


class _Microlog():
    def __init__(self):
        self.running = False

    def start(self, application: str = "", version: str = "", environment: str = ""):
        from microlog import log
        config.application = application
        config.version = version
        config.environment = environment
        if not self.running:
            log.start()
            self.startTracer()
            self.logEnvironment()
        self.running = True

    def logEnvironment(self):
        from microlog import debug
        lines = [
            "# Command line",
            f"{self.removeUser(sys.executable)} {' '.join(sys.argv)}",
            "# Environment",
        ] + [
            self.anonymize(key, value)
            for key, value in os.environ.items()
        ]
        debug("\n".join(lines))

    def anonymize(self, key, value):
        if value == os.environ["USER"]:
            value = "~"
        s = f" - {key}: {value}\n"
        return self.removeUser(s)
    
    def removeUser(self, s):
        return s.replace(os.path.expanduser("~"), "~")

    def startTracer(self):
        from microlog import tracer
        self.tracer = tracer.Tracer()
        self.tracer.start()

    def startServer(self):
        # Start the microlog server to easily preview microlog results locally
        import sys
        if not sys.argv[0].endswith("microlog/server.py"):
            from microlog import server
            server.run()

    def stop(self):
        if not self.running:
            return
        from microlog import log
        try:
            self.tracer.stop()
            self.tracer.join()
            log.log.stop()
            self.startServer()
        except Exception as e:
            sys.stderr.write(f"microlog.stop, error {e}")
        finally:
            self.running = False


_singleton = _Microlog()
start = _singleton.start
stop = _singleton.stop
_memory = models.Memory()

def heap():
    _memory.sample()


@atexit.register
def exit():
    stop()


class enabled():
        def __init__(self, *args, **argv):
            self.args = args
            self.argv = argv

        def __enter__(self):
            start(*self.args, **self.argv)
            return self

        def __exit__(self, *args):
            stop()
