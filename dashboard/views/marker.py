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
    model = Marker
    images = {
        api.config.EVENT_KIND_INFO:  js.jQuery("#marker-info"),
        api.config.EVENT_KIND_WARN:  js.jQuery("#marker-warn"),
        api.config.EVENT_KIND_DEBUG: js.jQuery("#marker-debug"),
        api.config.EVENT_KIND_ERROR: js.jQuery("#marker-error"),
    }
    offset = {
        api.config.EVENT_KIND_INFO:  0,
        api.config.EVENT_KIND_ERROR: 24,
        api.config.EVENT_KIND_WARN:  48,
        api.config.EVENT_KIND_DEBUG: 72,
    }
    instances = []

    def __init__(self, canvas, model):
        View.__init__(self, canvas, model)
        self.image = self.images[self.kind]
        self.x = self.when * config.PIXELS_PER_SECOND - self.canvas.fromScreenDimension(18)
        self.w = self.canvas.fromScreenDimension(36)
        self.h = self.canvas.fromScreenDimension(36)
        self.index = len(MarkerView.instances)
        MarkerView.instances.append(self)

    @classmethod
    def reset(cls):
        MarkerView.instances.clear()

    @classmethod
    def drawAll(cls, canvas, markers):
        for marker in markers:
            marker.draw()
 
    def offscreen(self):
        x = self.canvas.toScreenX(self.x)
        w = self.canvas.toScreenDimension(36)
        return w < 2 or x + w < 0 or x > self.canvas.width()
    
    @profiler.profile("Marker.draw")
    def draw(self):
        self.x = self.when * config.PIXELS_PER_SECOND - self.canvas.fromScreenDimension(18)
        self.y = 105 - self.offset[self.kind]
        self.w = self.canvas.fromScreenDimension(36)
        self.canvas.image(self.x, self.y, self.w, self.h, self.image, "#666", 3)

    def mouseenter(self, x, y):
        View.mouseenter(self, x, y)
        self.canvas.rect(self.x, self.y, self.w, self.h, color="white")

    def mouseleave(self, x, y):
        View.mouseleave(self, x, y)
        self.canvas.redraw()

    def formatStack(self, full=True):
        def shortFile(filename):
            parts = filename.split("/")
            if parts[-1] == "__init__.py":
                parts.pop()
            return parts[-1]
        def addLink(line):
            sections = line.replace('\\"', '"').split("#")
            filename, lineno = sections[:2]
            line = "#".join(sections[2:])
            where = line.split("\n")[0].strip()
            where = line.split("\n")[0].strip()
            what = "\\n".join(line.split("\n")[1:])
            if full:
                return f"<a href=vscode://file/{filename}:{lineno}:1>{where}</a>\n{what}\n"
            else:
                return f"<a href=vscode://file/{filename}:{lineno}:1>{shortFile(filename)}:{lineno}</a>\n"
        return ''.join([
              addLink(line.replace("<", "&lt;"))
              for line in self.stack
        ])

    def click(self, x, y):
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
            <br><br>
            <h2>Callstack</h2>
            <pre>{self.formatStack()}</pre>
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
