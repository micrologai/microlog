#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import collections
from typing import List
import microlog
from microlog.dashboard import canvas
from microlog.dashboard.views import config
from microlog.dashboard.dialog import dialog

def sanitize(text):
    return text.replace("<", "&lt;")


class Model():
    def load(self, event: list) -> None:
        pass


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
        self.model = self.model.load(event)
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
        pass

    def mousemove(self, x, y):
        pass

    def mouseleave(self, x, y):
        self.canvas.css("cursor", "default")
        dialog.hide()

    def __getattr__(self, name: str):
        return getattr(self.model, name)
        
    def inside(self, x, y):
        return not self.offscreen() and x >= self.x and x < self.x + self.w and y >= self.y and y < self.y + self.h
        
    def offscreen(self):
        x = self.canvas.toScreenX(self.x)
        w = self.canvas.toScreenDimension(self.w)
        return w < 3 or x + w < 0 or x > self.canvas.width()


def clear(canvas: microlog.dashboard.views.canvas.Canvas):
    from microlog.dashboard.views import status
    from microlog.dashboard.views import timeline
    from microlog.dashboard.views import call
    status.clear(canvas)
    timeline.clear(canvas)
    call.clear(canvas)



def draw(canvas: microlog.canvas.Canvas, views: List[View], timeline: microlog.dashboard.views.timeline.Timeline):
    clear(canvas)
    microlog.dashboard.views.status.StatusView.reset(canvas)
    for view in views:
        if not isinstance(view, microlog.dashboard.views.marker.MarkerView):
            view.drawIfVisible()
    for view in views:
        if isinstance(view, microlog.dashboard.views.marker.MarkerView):
            view.drawIfVisible()
    timeline.draw(canvas)