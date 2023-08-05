#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import js # type: ignore
import pyodide # type: ignore
from typing import List

import microlog
import microlog.api as api

from dashboard.dialog import dialog
from dashboard.views import View
from dashboard import config
from dashboard.views import sanitize

from microlog.models import Marker
from dashboard import markdown
from dashboard import profiler


class MarkerView(View):
    radius = 14
    model = Marker
    colors = {
        api.config.EVENT_KIND_INFO:  "#FFFF00",
        api.config.EVENT_KIND_WARN:  "#F97B41",
        api.config.EVENT_KIND_DEBUG: "#FF00FF",
        api.config.EVENT_KIND_ERROR: "#FF0000",
    }
    offset = {
        api.config.EVENT_KIND_INFO:  4,
        api.config.EVENT_KIND_ERROR: 28,
        api.config.EVENT_KIND_WARN:  53,
        api.config.EVENT_KIND_DEBUG: 76,
    }
    instances = []

    @profiler.profile("StatusView.__init__")
    def __init__(self, canvas, model):
        View.__init__(self, canvas, model)
        self.color = self.colors[self.kind]
        self.x = self.when * config.PIXELS_PER_SECOND - self.canvas.fromScreenDimension(self.radius / 2)
        self.w = self.canvas.fromScreenDimension(self.radius)
        self.h = self.canvas.fromScreenDimension(self.radius)
        self.index = len(MarkerView.instances)
        MarkerView.instances.append(self)

    @classmethod
    def reset(cls):
        MarkerView.instances.clear()

    @classmethod
    @profiler.profile("MarkerView.drawAll")
    def drawAll(cls, canvas, markers):
        for marker in markers:
            marker.draw()

    def getFullName(self):
        return self.callSite.name
    
    def getShortName(self):
        parts = self.callSite.name.split(".")
        name = parts[-1]
        if name == "<module>":
            name = parts[-2] or parts[-3]
        return name
 
    @profiler.profile("Marker.offscreen")
    def offscreen(self, scaleX, offsetX, width):
        self.x = self.when * config.PIXELS_PER_SECOND - self.canvas.fromScreenDimension(self.radius / 2)
        self.y = 105 - self.offset[self.kind]
        self.w = self.canvas.fromScreenDimension(self.radius)
        return View.offscreen(self, scaleX, offsetX, width)
    
    @profiler.profile("Marker.draw")
    def draw(self):
        self.x = self.when * config.PIXELS_PER_SECOND - self.canvas.fromScreenDimension(self.radius / 2)
        self.y = 105 - self.offset[self.kind]
        self.w = self.canvas.fromScreenDimension(self.radius)
        self.canvas.circle(self.x + self.w / 2, self.y + self.radius / 2, self.w / 2, self.color, 1, "black")

    def mouseenter(self, x, y):
        View.mouseenter(self, x, y)
        self.select()
    
    def select(self):
        self.draw()
        (js.jQuery("#marker-highlight")
            .attr("index", self.index)
            .css("left", self.canvas.toScreenX(self.x))
            .css("top", self.canvas.toScreenY(self.y) + 42)
            .appendTo(self.canvas.canvas.parent()))

    def mouseleave(self, x, y):
        View.mouseleave(self, x, y)

    def formatStack(self, full=True):
        def shortFile(filename):
            parts = filename.split("/")
            if parts[-1] == "__init__.py":
                parts.pop()
            return parts[-1]
        def addLink(callSite):
            return f"<a href=vscode://file/{callSite.filename}:{callSite.lineno}:1>{shortFile(callSite.filename)}:{callSite.lineno}</a>\n"
        return ''.join([
              addLink(callSite)
              for callSite in self.stack
        ])

    def click(self, x, y):
        self.select()
        formattedStack = self.formatStack()
        stack = f"""
            <h2>Callstack</h2>
            <pre>{formattedStack}</pre>
        """ if formattedStack else ""

        html = f"""
            <button id='prev-marker'>&lt;</button>
            Log entry {self.index + 1} of {len(MarkerView.instances)}
            <button id='next-marker'>&gt;</button>
            &nbsp; &nbsp; &nbsp; &nbsp;
            {microlog.config.kinds[self.kind]}
            @ {self.when:.3f}s
            &nbsp; &nbsp; &nbsp; &nbsp;
            <button id='show-log'>show full log</button>
            <br><br>
            {markdown.toHTML(self.message)}
            {stack}
        """
        dialog.show(self.canvas, x, y, html)
        js.jQuery("#prev-marker").click(
            pyodide.ffi.create_proxy(lambda event:
                self.index and MarkerView.instances[self.index - 1].click(x, y)))
        js.jQuery("#next-marker").click(
            pyodide.ffi.create_proxy(lambda event: 
                self.index < len(MarkerView.instances) and MarkerView.instances[self.index + 1].click(x, y)))
        js.jQuery("#show-log").click(
            pyodide.ffi.create_proxy(lambda event:
                self.showLog()))
    
    def showLog(self):
        dialog.hide()
        js.jQuery('a[href="#tabs-log"]').click()


def clickMarker(event):
    index = int(js.jQuery("#marker-highlight").attr("index"))
    x = event.originalEvent.offsetX
    y = event.originalEvent.offsetY
    MarkerView.instances[index].click(x, y)


js.jQuery("#marker-highlight").click(pyodide.ffi.create_proxy(clickMarker))