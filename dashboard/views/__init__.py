#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import collections
import js # type: ignore
from dashboard import config
from dashboard import profiler

def sanitize(text):
    return text.replace("<", "&lt;").replace("\\n", "<br>")


class Model():
    pass


class View():
    model = None
    canvas = None
    x: float
    y: float
    w: float
    h: float

    @profiler.profile("View.__init__")
    def __init__(self, canvas, model):
        self.canvas = canvas
        self.model = model
        self.x = self.when * config.PIXELS_PER_SECOND
        self.y = 0
        self.w = self.duration * config.PIXELS_PER_SECOND
        self.h = 0    

    def __eq__(self, other):
        return not self is other

    def draw(self):
        pass

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
        return x >= self.x and x < self.x + self.w and y >= self.y and y < self.y + self.h
        
    def offscreen(self, scaleX, offsetX, width):
        x = self.x * scaleX + offsetX
        w = self.w * scaleX
        return w < 2 or x + w < 0 or x > width
    
    def slowImport(self):
        return self.depth > 0 and self.duration > 0.1 and self.isImport()

    def isImport(self):
        return self.callSite.name.endswith("<module>") 

    def getFullName(self):
        return f"😡 {self.callSite.name}" if self.slowImport() else self.callSite.name
    
    def getShortName(self):
        parts = self.callSite.name.split(".")
        name = parts[-1]
        if name == "<module>":
            name = parts[-2] or parts[-3]
        return f"😡 {name}" if self.slowImport() else name

    def modifyColor(self, color, offset):
        rgb_hex = [color[x:x+2] for x in [1, 3, 5]]
        new_rgb_int = [
            int(min(255, max(0, int(hex_value, 16) + offset)))
            for hex_value in rgb_hex
        ]
        return "#" + "".join([hex(i)[2:] for i in new_rgb_int])
