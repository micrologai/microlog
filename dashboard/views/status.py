#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

from dashboard import canvas
from dashboard.views import View
import dashboard.config as config
import dashboard.dialog as dialog
import js # type: ignore

from microlog.models import Status
from microlog.models import toGB
from dashboard import profiler

class StatusView(View):
    model = Status
    instances = []
    
    @profiler.profile("StatusView.__init__")
    def __init__(self, canvas: canvas.Canvas, model):
        View.__init__(self, canvas, model)
        self.h = config.STATS_HEIGHT
        self.previous = None
        StatusView.instances.append(self)

    @classmethod
    def reset(cls):
        StatusView.instances.clear()
        js.jQuery("#summary").css("display", "none")

    def inside(self, x, y):
        if not self.previous:
            return False
        return x >= self.previous.x and x < self.x and y >= self.y and y < self.y + self.h

    @classmethod
    @profiler.profile("StatusView.drawAll")
    def drawAll(cls, canvas: canvas.Canvas, views):
        if views:
            canvas.clear("#222")
            cls.drawCpu(canvas, views)
            cls.drawMemory(canvas, views)
            cls.drawModules(canvas, views)
            previous = None
            for view in views:
                view.previous = previous
                previous = view

    @classmethod
    def drawModules(cls, canvas: canvas.Canvas, views):
        maxModuleCount = max(view.moduleCount for view in views)
        points = cls.getPoints(views, lambda status: status.moduleCount, maxModuleCount, 20)
        canvas.polygon(points, 2, "#f6ff00AA")

    @classmethod
    def drawMemory(cls, canvas: canvas.Canvas, views):
        maxMemory = max(view.memory for view in views)
        points = cls.getPoints(views, lambda status: status.memory, maxMemory, 10)
        canvas.polygon(points, 3, "#DD0000AA")

    @classmethod
    def drawCpu(cls, canvas: canvas.Canvas, views):
        y = config.STATS_OFFSET_Y + config.STATS_HEIGHT
        linePoints = cls.getPoints(views, lambda status: 1.1 * (status.cpu - 10), 100, 5)
        canvas.polygon(linePoints, 1, "#549f56")
        fillPoints = [
            ( views[0].x, y )
        ] + linePoints + [
            ( views[-1].x, y ),
            ( views[0].x, y )
        ]
        canvas.region(fillPoints, "#244424")

    @classmethod
    @profiler.profile("StatusView.getPoints")
    def getPoints(cls, views, getValue, maxValue, offset):
        H = config.STATS_HEIGHT
        Y = config.STATS_OFFSET_Y + config.STATS_HEIGHT
        points = []
        for status in views:
            x = round(status.x)
            y = round(Y - getValue(status) * (H - offset * 2) / (maxValue + 1) - 5)
            if len(points) > 2 and points[-1][1] == points[-2][1] == y:
                points.pop()
            points.append((x, y))
        return points

    @profiler.profile("View.offscreen")
    def offscreen(self, scaleX, offsetX, width):
        x = self.x * scaleX + offsetX
        w = self.w * scaleX
        offset = scaleX * width / 2
        return x + w < -offset or x > width + offset

    def mousemove(self, x, y):
        cpu = (self.previous.cpu + self.cpu) / 2 if self.previous else self.cpu
        rows = f"""
            <tr class="header"><td>Metric</td><td>Value</td><td>Line Color</td></tr>
            <tr><td>CPU</td> <td>{round(cpu)}%</td> <td>Green</td> </tr>
            <tr><td>Module Count</td> <td>{self.moduleCount:,}</td> <td>Yellow</td></tr>
            <tr><td>Memory</td> <td>{toGB(self.memory)}</td> <td>Red</td></tr>
        """
        html = f"""
            Process Statistics at {self.previous.when:.3f}s<br>
            <table style="border-collapse: collapse;">
            {rows}
            </table>
        """
        top = js.jQuery(".tabs-header").height() + 25
        js.jQuery("#summary").css("display", "block").css("top", top).html(html)
        self.showHairline(x)

    def showHairline(self, x):
        js.jQuery("#hairline") \
            .css("display", "block") \
            .css("top", js.jQuery(".tabs-header").height() + 3) \
            .css("left", self.canvas.toScreenX(x) - 3) \
            .css("height", config.STATS_HEIGHT)

    def __str__(self):
        return f"cpu: {round(self.cpu)}%, memory: {toGB(self.memory)}, modules: {round(self.moduleCount)}"
