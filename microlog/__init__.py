#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import os
import time

from microlog import settings
from microlog import config
from microlog import memory
from microlog import server
from microlog import status
from microlog import tracer
from microlog import collector 
from microlog.config import micrologAPI

from microlog.memory import heap
from microlog.memory import toGB


def info(*args):
    _log(config.EVENT_KIND_INFO, *args)


def warn(*args):
    _log(config.EVENT_KIND_WARN, *args)


def debug(*args):
    _log(config.EVENT_KIND_DEBUG, *args)


def error(*args):
    _log(config.EVENT_KIND_ERROR, *args)


@micrologAPI
def trace(function):
    from microlog import events
    from microlog import span
    import functools
    import inspect

    def getModuleName(function):
        module = inspect.getmodule(function)
        moduleName = module.__name__
        if moduleName == "__main__" and hasattr(module, "__file__"):
            moduleName = os.path.basename(module.__file__).replace(".py", "").replace(".pyc", "")
        return moduleName

    @functools.wraps(function)
    def tracedFunction(*args, **argv):
        arguments = span.freezeArguments(function, args, argv)
        start = events.now()
        try:
            return function(*args, **argv)
        finally:
            span.Span(
                start,
                f"{getModuleName(function)}.{function.__name__}",
                events.now() - start,
                arguments,
            ).save()
    return tracedFunction


@micrologAPI
def _log(kind, *args):
    import inspect
    import traceback
    import os
    from microlog import events
    from microlog import marker
    when = events.now()
    message = " ".join([ str(arg) for arg in args ])
    stack = list(f"{os.path.abspath(frame.filename)}#{frame.lineno}#{line}" for frame, line in zip(reversed(inspect.stack()), traceback.format_stack()))
    if "/microlog/" in stack[-1]:
        stack = []
    marker.MarkerModel(kind, when, message, stack).save()



class Runner():
    def __init__(self):
        import inspect
        _ = inspect.stack()
        self.statusGenerator = status.StatusGenerator()
        self.tracer = tracer.Tracer()
        self.collector = collector.FileCollector()
        self.running = False

    @micrologAPI
    def start(self, application: str = "",
            version: str = "",
            environment: str = "",
            info: str = "",
            traceDelay: float = 0.005,
            statusDelay: float = 0.01,
            showInBrowser=False,
            verbose=False):
        self.running = True
        import atexit
        
        settings.current.application = application
        settings.current.version = version
        settings.current.environment = environment
        settings.current.info = info
        settings.current.traceDelay = traceDelay
        settings.current.statusDelay = statusDelay
        settings.current.verbose = verbose

        self.showInBrowser = showInBrowser
        self.verbose = verbose

        for thread in [ self.statusGenerator, self.tracer, self.collector ]:
            thread.start()

        @atexit.register
        def exit():
            self.stop()

    @micrologAPI
    def stop(self):
        if not self.running:
            return
        self.running = False
        start = time.time()
        for thread in [ self.statusGenerator, self.tracer, self.collector ]:
            thread.stop()
        end = time.time()
        config.totalPostProcessing = end - start
        if self.showInBrowser:
            self.showLog(self.collector.identifier)
        if self.verbose:
            print(config.statistics())

    def showLog(self, identifier):
        import webbrowser
        os.system(f"python3 {server.__file__} &")
        webbrowser.open(f"http://127.0.0.1:4000/log/{identifier}")


runner = Runner()
start = runner.start
stop = runner.stop

class enabled:
        def __init__(self, *args, **argv):
            self.args = args
            self.argv = argv

        def __enter__(self):
            start(*self.args, **self.argv)
            return self

        def __exit__(self, *args):
            stop()