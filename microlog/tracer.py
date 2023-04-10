#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
import threading
import time

from microlog import settings
from microlog import events
from microlog import stack

from microlog.config import micrologBackgroundService

class Tracer(threading.Thread):
    def start(self) -> None:
        self.setDaemon(True)
        self.stack = stack.Stack()
        self.mainThread = threading.currentThread().ident
        return super().start()

    def run(self) -> None:
        while True:
            self.sample()
            time.sleep(settings.current.traceDelay)

    def getMainStackFrame(self):
        for ident, frame in sys._current_frames().items():
            if ident == self.mainThread:
                return frame

    @micrologBackgroundService("Tracer")
    def sample(self) -> None:
        self.merge(self.getStack(events.now(), self.getMainStackFrame()))

    def getStack(self, when, frame):
        return stack.Stack(when, frame)

    def merge(self, stack: stack.Stack):
        caller = None
        for call1, call2 in zip(self.stack, stack):
            if call1 == call2:
                call2.when = call1.when
            else:
                call1.save(stack.when, caller)
            caller = call1
        if self.stack and len(self.stack) > len(stack):
            caller = self.stack[len(stack) - 1]
            for call in self.stack[len(stack):]:
                call.save(stack.when, caller)
                caller = call
        self.stack = stack

    def stop(self):
        self.merge(stack.Stack(events.now()))

    