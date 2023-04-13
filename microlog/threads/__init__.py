#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import cProfile
import threading
import time

from microlog import config


class BackgroundThread(threading.Thread):
    def start(self):
        self.profiler = cProfile.Profile()
        return threading.Thread.start(self)

    def run(self) -> None:
        while True:
            self.profiler.enable()
            self.tick()
            self.profiler.disable()
            if self.delay:
                time.sleep(self.delay)

    def storeOverhead(self):
        import io
        import pstats
        string = io.StringIO()
        pstats.Stats(self.profiler, stream=string).sort_stats(pstats.SortKey.CUMULATIVE).print_stats()
        for line in string.getvalue().split("\n"):
            if "/microlog/" in line:
                _, _, _, cumulativeTime, *_ = line.split()
                config.totalBackgroundOverhead[self.__class__.__name__] = float(cumulativeTime)
                return

