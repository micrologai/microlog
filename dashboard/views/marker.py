#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import js # type: ignore
from typing import List

import microlog.api as api

from dashboard.dialog import dialog
from dashboard.views import View
from dashboard import config
from dashboard.views import sanitize

from microlog.models import MarkerModel
from dashboard import markdown
from dashboard import profiler


class MarkerView(View):
    model = MarkerModel
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

    def __init__(self, canvas, event):
        View.__init__(self, canvas, event)
        self.image = self.images[self.kind]
        self.x = self.when * config.PIXELS_PER_SECOND - self.canvas.fromScreenDimension(18)
        self.w = self.canvas.fromScreenDimension(36)
        self.h = self.canvas.fromScreenDimension(36)

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
        self.canvas.rect(self.x, self.y, self.w, self.h)

    def mouseleave(self, x, y):
        View.mouseleave(self, x, y)
        self.canvas.redraw()

    def formatStack(self, full=True):
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
                return f"<a href=vscode://file/{filename}:{lineno}:1>{filename.split('/')[-1]}:{lineno}</a>\n"
        return ''.join([
              addLink(line.replace("<", "&lt;"))
              for line in self.stack
        ])

    def click(self, x, y):
        html = f"""
            At {self.when:.3f}s<br>
            {markdown.toHTML(self.message)}
            <br><br>
            <h1>Callstack</h1>
            <pre>{self.formatStack()}</pre>
        """
        dialog.show(self.canvas, x, y, html)
