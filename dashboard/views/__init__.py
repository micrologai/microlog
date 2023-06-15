#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import collections
import js # type: ignore
from typing import List
import microlog.microlog as microlog
from dashboard import canvas
from dashboard.views import config
from dashboard.dialog import dialog
from dashboard.views.timeline import Timeline

def sanitize(text):
    return text.replace("<", "&lt;").replace("\\n", "<br>")


class Model():
    def unmarshall(self, event: list) -> None:
        return self


class View():
    model: Model = None
    instances = collections.defaultdict(list)
    canvas: canvas.Canvas
    x: float
    y: float
    w: float
    h: float

    def __init__(self, canvas, event):
        self.canvas = canvas
        self.model = self.model.unmarshall(event)
        self.kind = event[0]
        self.x = self.when * config.PIXELS_PER_SECOND
        self.y = 0
        self.w = self.duration * config.PIXELS_PER_SECOND
        self.h = 0    
        View.instances[self.__class__].append(self)

    def __eq__(self, other):
        return not self is other

    def others(self):
        return View.instances[self.__class__]

    def draw(self):
        pass

    def drawIfVisible(self):
        if not self.offscreen():
            self.draw()

    def mouseenter(self, x, y):
        self.canvas.css("cursor", "pointer")

    def mousemove(self, x, y):
        pass

    def click(self, x, y):
        pass

    def mouseleave(self, x, y):
        self.canvas.css("cursor", "default")

    def __getattr__(self, name: str):
        return getattr(self.model, name)
        
    def inside(self, x, y):
        return not self.offscreen() and x >= self.x and x < self.x + self.w and y >= self.y and y < self.y + self.h
        
    def offscreen(self):
        x = self.canvas.toScreenX(self.x)
        w = self.canvas.toScreenDimension(self.w)
        return w < 3 or x + w < 0 or x > self.canvas.width()

    def modifyColor(self, color, offset):
        rgb_hex = [color[x:x+2] for x in [1, 3, 5]]
        new_rgb_int = [
            int(min(255, max(0, int(hex_value, 16) + offset)))
            for hex_value in rgb_hex
        ]
        return "#" + "".join([hex(i)[2:] for i in new_rgb_int])

    def toHTML(self, markdownText):
        import textwrap
        prevIndent = -1
        html = []
        fenced = False
        for lineno, line in enumerate(textwrap.dedent(markdownText).split("\\n"), 1):
            if line.strip() in ["---", "```"]:
                if fenced:
                    html.append("</pre>")
                    fenced = False
                else:
                    fenced = True
                    html.append("<pre>")
                continue

            if fenced:
                for n in range(prevIndent):
                    if line and line[0] == " ":
                        line = line[1:]
                html.append(line)
                html.append("<br>")
                continue

            indent = prevIndent
            if line:
                indent = 0
                while line and line[0] == " ":
                    indent += 1
                    line = line[1:]
            if indent > prevIndent and prevIndent != -1:
                html.append("<ul style='margin-block-start: 0; margin-bottom: 20px'>")
            if indent < prevIndent:
                html.append("</ul>")

            if line == "":
                if html and not html[-1].startswith("<"):
                    html.append("<br><br>")
            elif len(line) > 3 and line[0:3] == "###":
                html.append(f"<h3>{line[3:].strip()}</h3>")
            elif len(line) > 2 and line[0:2] == "##":
                html.append(f"<h2>{line[2:].strip()}</h2>")
            elif line[0] == "#":
                html.append(f"<h1>{line[1:].strip()}</h1>")
            elif line[0] == "-":
                html.append(f"<li>{line[1:]}</li>")
            else:
                html.append(f"{line}<br>")
            prevIndent = indent
        html.append("</h1>")
        html.append("</h2>")
        html.append("</h3>")
        html.append("</ul>")
        return "".join(html)


def draw(canvas: microlog.canvas.Canvas, views: List[View], timeline: Timeline):
    from dashboard.views.marker import MarkerView
    from dashboard.views.call import CallView
    from dashboard.views.status import StatusView
    try:
        visible = [view for view in views if not view.offscreen()]
        StatusView.drawAll(canvas, [view for view in visible if isinstance(view, StatusView)])
        CallView.drawAll(canvas, [view for view in visible if isinstance(view, CallView)])
        MarkerView.drawAll(canvas, [view for view in visible if isinstance(view, MarkerView)])
        timeline.draw(canvas)
    except Exception as e:
        import traceback
        stack = traceback.format_exc().replace("\n", "<br>")
        error = f"Internal error: {stack}"
        dialog.show(canvas, 100, 100, error)
        raise e