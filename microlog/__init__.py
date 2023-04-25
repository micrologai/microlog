#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import functools
import inspect
import os
import time


from microlog import config
from microlog import memory
from microlog import settings
from microlog.threads import status

from microlog.config import micrologAPI
from microlog.memory import heap


def info(*args):
    _log(config.EVENT_KIND_INFO, *args)


def warn(*args):
    _log(config.EVENT_KIND_WARN, *args)


def debug(*args):
    _log(config.EVENT_KIND_DEBUG, *args)


def error(*args):
    _log(config.EVENT_KIND_ERROR, *args)


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
    marker.MarkerModel(kind, when, message, stack).marshall()


class Runner():
    @micrologAPI
    def start(self, application: str = "",
            version: str = "",
            environment: str = "",
            info: str = "",
            traceDelay: float = 0.005,
            statusDelay: float = 0.01,
            showInBrowser=False,
            verbose=False):
        import atexit
        import inspect
        from microlog.threads import tracer
        from microlog.threads import collector 

        _ = inspect.stack()
        self.statusGenerator = status.StatusGenerator()
        self.tracer = tracer.Tracer()
        self.collector = collector.FileCollector()
        
        settings.current.application = application
        settings.current.version = version
        settings.current.environment = environment
        settings.current.info = info
        settings.current.traceDelay = traceDelay
        settings.current.statusDelay = statusDelay
        settings.current.verbose = verbose

        self.showInBrowser = showInBrowser
        self.verbose = verbose

        @atexit.register
        def exit():
            self.stop()

        for thread in [ self.statusGenerator, self.collector, self.tracer ]:
            thread.start()
        self.running = True

    @micrologAPI
    def stop(self):
        memory.stop()
        if not self.running:
            return
        self.running = False
        start = time.time()
        for thread in [ self.tracer, self.statusGenerator, self.collector ]:
            thread.stop()
            thread.storeOverhead()
        end = time.time()
        config.totalPostProcessing = end - start
        if self.showInBrowser:
            self.showLog(self.collector.identifier)
        if self.verbose:
            print(config.statistics())

    def showLog(self, identifier):
        import webbrowser
        from microlog import server
        os.system(f"python3 {server.__file__} &")
        webbrowser.open(f"http://127.0.0.1:4000/log/{identifier}")


runner = Runner()
start = runner.start
stop = runner.stop


@micrologAPI
def trace(functionOrClass):
    """
    Always trace a function or class, even when the sampling trace might miss it.
    """
    if inspect.isclass(functionOrClass):
        cls = functionOrClass
        methods = [
            name
            for name in dir(cls)
            if callable(getattr(cls, name)) and (name == "__init__" or not name.startswith("__"))
        ]
        for methodName in methods:
            setattr(cls, methodName, trace(getattr(cls, methodName)))
        return cls
    else:
        function = functionOrClass

        @functools.wraps(function)
        def tracedFunction(*args, **argv):
            runner.tracer.sample(function)
            try:
                return function(*args, **argv)
            finally:
                runner.tracer.sample(function)

        return tracedFunction


class enabled():
        def __init__(self, *args, **argv):
            self.args = args
            self.argv = argv

        def __enter__(self):
            start(*self.args, **self.argv)
            return self

        def __exit__(self, *args):
            stop()


class disabled():
        def __init__(self, *args, **argv):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass