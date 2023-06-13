#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import js
from typing import List

import microlog.microlog as microlog

from dashboard.dialog import dialog
from dashboard.views import View
from dashboard.views import config
from dashboard.views import sanitize

from microlog.models import MarkerModel
from dashboard import colors
from dashboard import profiler


class MarkerView(View):
    model = MarkerModel
    images = {
        microlog.config.EVENT_KIND_INFO:  js.jQuery("#marker-info"),
        microlog.config.EVENT_KIND_WARN:  js.jQuery("#marker-warn"),
        microlog.config.EVENT_KIND_DEBUG: js.jQuery("#marker-debug"),
        microlog.config.EVENT_KIND_ERROR: js.jQuery("#marker-error"),
    }
    offset = {
        microlog.config.EVENT_KIND_INFO:  0,
        microlog.config.EVENT_KIND_ERROR: 24,
        microlog.config.EVENT_KIND_WARN:  48,
        microlog.config.EVENT_KIND_DEBUG: 72,
    }

    def __init__(self, canvas, event):
        View.__init__(self, canvas, event)
        self.image = self.images[self.kind]
        size = self.canvas.fromScreenDimension(36)
        self.x = self.when * config.PIXELS_PER_SECOND - size / 2

    @classmethod
    def drawAll(cls, canvas, calls):
        for call in calls:
            call.draw()
 
    @profiler.profile("Call.draw")
    def draw(self):
        color = colors.getColor(self.callSite.name)
        adjustment = 2 * self.depth
        self._draw(self.modifyColor(color, -adjustment), self.modifyColor("#111111", adjustment))
    
    def _draw(self, fill, color):
        w = self.canvas.toScreenDimension(self.w)
        if w > 0:
            self.canvas.fillRect(self.x, self.y, self.w, self.h - 1, fill)
            self.canvas.line(self.x, self.y, self.x + self.w, self.y, 1, "#DDD")
            self.canvas.line(self.x, self.y, self.x, self.y + self.h, 1, "#AAA")
        if w > 25:
            dx = self.canvas.fromScreenDimension(4)
            self.canvas.text(self.x + dx, self.y + 2, self.getLabel(), color, self.w)
 
    def offscreen(self):
        x = self.canvas.toScreenX(self.x)
        w = self.canvas.toScreenDimension(self.w)
        return w < 2 or x + w < 0 or x > self.canvas.width()
    
    @profiler.profile("Marker.draw")
    def draw(self):
        size = self.canvas.fromScreenDimension(36)
        self.x = self.when * config.PIXELS_PER_SECOND - size / 2
        self.y = 105 - self.offset[self.kind]
        self.w = size
        self.h = 36
        self.canvas.image(self.x, self.y, self.w, self.h, self.image, "white", 0)

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

    def mousemove(self, x, y):
        html = f"""
            At {self.when:.3f}s<br>
            {self.toHTML(self.message)}
            <br><br>
            <h1>Callstack</h1>
            <pre>{self.formatStack()}</pre>
        """
        dialog.show(self.canvas, x, y, html)
