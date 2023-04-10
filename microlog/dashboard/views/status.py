#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import microlog.dashboard.views as views
import microlog.dashboard.views.config as config
from microlog.dashboard.dialog import dialog

from microlog.status import Status
from microlog import profiler

class StatusView(views.View):
    model = Status
    next = None
    previous = None
    maxModuleCount = 0
    
    def __init__(self, canvas, event):
        views.View.__init__(self, canvas, event)
        StatusView.maxModuleCount = max(self.python.moduleCount, StatusView.maxModuleCount)
        self.previous = StatusView.previous
        if self.previous:
            self.duration = self.when - self.previous.when
            self.x = self.previous.when * config.PIXELS_PER_SECOND
            self.previous.next = self
        self.w = self.duration * config.PIXELS_PER_SECOND
        self.h = config.STATS_HEIGHT
        StatusView.previous = self
    
    @classmethod
    def reset(cls, canvas):
        cls.previous = cls(canvas, [0, 0, [0, 0, 0], [0], [0] ])
        cls.previous.x = 0
        cls.previous.w = 1

    @profiler.profile("Status.draw")
    def draw(self):
        if self.previous:
            self.statline(
                self.previous.x, self.previous.process.cpu,
                self.x, self.process.cpu,
                100, 5, 1, "#549f56", "#244424")
            self.statline(
                self.previous.x, self.previous.python.moduleCount,
                self.x, self.python.moduleCount,
                StatusView.maxModuleCount, 20, 2, "#f6ff00AA")

    def statline(self, x1, value1, x2, value2, maxValue, marginTop, width, color, fill=None):
        y1 = self.getY(value1, maxValue, marginTop)
        y2 = self.getY(value2, maxValue, marginTop)
        y = config.STATS_OFFSET_Y + config.STATS_HEIGHT
        if fill:
            self.canvas.region([ [x1, y1], [x2, y2], [x2, y], [x1, y], [x1, y1] ], fill, 1, fill)
        self.canvas.line(x1, y1, x2, y2, width, color)

    def getY(self, value, maxValue, marginTop):
        y = config.STATS_OFFSET_Y + config.STATS_HEIGHT - value * (config.STATS_HEIGHT - marginTop * 2) / (maxValue + 1) - 5
        return max(0, min(config.STATS_HEIGHT, y))

    def offscreen(self):
        x = self.canvas.toScreenX(self.previous.x if self.previous else self.x)
        w = self.canvas.toScreenDimension(self.w)
        offscreen = x + w < 0 or x > self.canvas.width()
        return offscreen

    def mousemove(self, x, y):
        cpu = (self.process.cpu + self.next.process.cpu) / 2 if self.next else self.process.cpu
        html = f"""
            At: {self.previous.when:.3f}s<br>
            CPU: {cpu:.2f}%<br>
            Modules: {self.python.moduleCount:,}<br>
        """
        dialog.show(self.canvas, x, y, html)



def clear(canvas):
    x, w = canvas.absolute(0, canvas.width())
    canvas.rect(x, 0, w, config.STATS_HEIGHT, "black", 0, "")