#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import js
from typing import List

import microlog

from microlog.dashboard.dialog import dialog
from microlog.dashboard.views import View
from microlog.dashboard.views import config

from microlog.marker import MarkerModel


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

    @microlog.profiler.profile("Marker.draw")
    def draw(self):
        size = self.canvas.fromScreenDimension(36)
        self.x = self.when * config.PIXELS_PER_SECOND - size / 2
        self.y = 105 - self.offset[self.kind]
        self.w = size
        self.h = 36
        self.canvas.image(self.x, self.y, self.w, self.h, self.image, "white", 0)

    def mousemove(self, x, y):
        def addLink(line):
            sections = line.split("#")
            filename, lineno = sections[:2]
            rest1, rest2, _ = "#".join(sections[2:]).split("\n")
            return f"<a href=vscode://file/{filename}:{lineno}:1>{rest1.strip()}</a>\n{rest2}\n"
        stack = [
              addLink(line.replace("<", "&lt;"))
              for line in self.stack
        ]
        html = f"""
            {self.message}<br>
            At {self.when:.3f}s<br>
            <pre>{''.join(stack)}</pre>
        """
        dialog.show(self.canvas, x, y, html)
