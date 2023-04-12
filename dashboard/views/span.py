#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import json
from typing import List

from microlog.span import Span
from microlog import profiler
from dashboard import colors
from dashboard.views import sanitize
from dashboard.views import View
from dashboard.dialog import dialog

        
class SpanView(View):
    model = Span
    _previous = None
    spanHeight = 20
    depth = 0

    def __init__(self, canvas, event):
        View.__init__(self, canvas, event)
        self.previous = SpanView._previous
        self.label = f"{self.name} at {round(self.when, 3)}s for {round(self.duration, 3)}s"
        if self.previous and self.when < self.previous.when:
            self.depth = self.previous.depth + 1
        self.h = self.spanHeight
        SpanView._previous = self
    
    @profiler.profile("Span.draw")
    def draw(self):
        self.y = self.canvas.height() * 0.9 - self.depth * (self.h + 2)
        self.canvas.rect(self.x, self.y, self.w, self.h, colors.getColor(self.name), 1, "gray")
        self.canvas.text(self.x + self.canvas.fromScreenDimension(5), self.y, self.label, "black", self.w, "12px Arial")

    def mousemove(self, x, y):
        dialog.show(self.canvas, x, y, f"""
            <b>{sanitize(self.name).replace("..",".")}</b><br>
            This span started at: {self.when}s<br>
            Duration: {self.duration}s<br>
            {self.formatArguments()}
        """)

    @classmethod
    def reset(cls, canvas):
        cls.previous = None 

    def formatArguments(self):
        rows = "".join(
            f"""
                <tr>
                    <td width=120>{kv[0]}</td>
                    <td width=120>{kv[1].replace('<', '&lt;') if isinstance(kv[1], str) else kv[1]}</td>
                </tr>
            """
            for kv in json.loads(json.loads(self.arguments))
        )
        return f"""
                <span>
                    Function Parameters:
                    <hr>
                    <table>
                        <tr class="header"><td>Name</td><td>Value</td></tr>
                        {rows}
                    </table>
                </span>
            """ if rows else ""
