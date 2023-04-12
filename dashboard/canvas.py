#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import math
import js
import pyodide

import microlog.profiler as profiler

jquery = js.jQuery

class Canvas():
    def __init__(self, elementId, redrawCallback) -> None:
        self.scale = 1
        self.offset = 24
        self.redrawCallback = redrawCallback
        self.canvas = jquery(elementId)
        self.context = self.canvas[0].getContext("2d")
        self.canvas \
            .on("mousedown", pyodide.ffi.create_proxy(lambda event: self.mousedown(event))) \
            .on("mousemove", pyodide.ffi.create_proxy(lambda event: self.mousemove(event))) \
            .on("mouseleave", pyodide.ffi.create_proxy(lambda event: self.mouseup(event))) \
            .on("mouseup", pyodide.ffi.create_proxy(lambda event: self.mouseup(event))) \
            .on("mousewheel", pyodide.ffi.create_proxy(lambda event: self.mousewheel(event)))
        self.dragX = 0
        self.maxX = 0
        self._width = self.canvas.parent().width()
        self._height = self.canvas.parent().height()
        jquery(js.window).on("resize", pyodide.ffi.create_proxy(lambda event: self.redraw()))
        js.setTimeout(pyodide.ffi.create_proxy(lambda: self.redraw()), 1)

    def mousedown(self, event):
        from dashboard.dialog import dialog
        self.dragX = event.originalEvent.pageX
        dialog.hide()

    def isDragging(self):
        return self.dragX != 0

    def mousemove(self, event):
        if self.isDragging():
            dx = event.originalEvent.pageX - self.dragX
            if self.offset + dx < self.width() * 0.9:
                self.dragX = event.originalEvent.pageX
                self.drag(dx, event)
            event.preventDefault()
    
    def drag(self, dx, event):
        self.offset += dx
        self.redraw()

    def mouseup(self, event):
        self.dragX = 0

    def mousewheel(self, event):
        event.preventDefault()
        x = event.originalEvent.offsetX
        y = event.originalEvent.offsetY
        self.zoom(x, 2 if event.originalEvent.wheelDelta > 0 else 0.5, event)

    def on(self, event, callback):
        self.canvas.on(event, pyodide.ffi.create_proxy(lambda event: callback(event)))
        return self

    def css(self, key, value):
        self.canvas.css(key, value)

    def zoom(self, x, scaleFactor, event):
        offset = x - (scaleFactor * (x - self.offset))
        self.offset = min(self.width() * 0.9, offset)
        self.scale = self.scale * scaleFactor
        self.redraw()
    
    def width(self):
        return self._width

    def height(self):
        return self._height

    def toScreenX(self, x):
        return x * self.scale + self.offset

    def fromScreenX(self, x):
        return x - self.offset / self.scale

    def toScreenDimension(self, w):
        return w * self.scale

    def fromScreenDimension(self, w):
        return w / self.scale

    def redraw(self, event=None):
        self._width = self.canvas.parent().width()
        self._height = self.canvas.parent().height()
        self.canvas.attr("width", self._width).attr("height", self._height)
        self.redrawCallback(event)

    @profiler.profile("Canvas.line")
    def line(self, x1:float, y1:float, x2:float, y2:float, lineWidth=1, color="black"):
        x1 = round(x1 * self.scale + self.offset)
        x2 = round(x2 * self.scale + self.offset)
        self.context.strokeStyle = color
        self.context.lineWidth = lineWidth
        self.context.beginPath()
        self.context.moveTo(x1, y1)
        self.context.lineTo(x2, y2)
        self.context.stroke()

    @profiler.profile("Canvas.region")
    def region(self, points, fill="white", lineWidth=1, color="black"):
        self.context.beginPath()
        self.context.moveTo(round(points[0][0] * self.scale + self.offset), points[0][1])
        for x, y in points[1:]:
            x = round(x * self.scale + self.offset)
            self.context.lineTo(x, y)
        self.context.strokeStyle = color
        self.context.lineWidth = lineWidth
        self.context.stroke()
        self.context.fillStyle = fill
        self.context.fill()

    @profiler.profile("Canvas.rect")
    def rect(self, x:float, y:float, w:float, h:float, fill="white", lineWidth=1, color="black"):
        x = round(x * self.scale + self.offset)
        w = round(w * self.scale)
        self.context.fillStyle = fill
        self.context.fillRect(x, y, w, h)
        if lineWidth:
            self.context.strokeStyle = color
            self.context.lineWidth = lineWidth
            self.context.beginPath()
            self.context.rect(x, y, w, h)
            self.context.stroke()

    @profiler.profile("Canvas.rect")
    def image(self, x:float, y:float, w:float, h:float, jqueryImage, shadowColor=None, shadowBlur=0):
        x = round(x * self.scale + self.offset)
        w = round(w * self.scale)
        h = round(h)
        if shadowBlur:
            self.context.shadowColor = shadowColor
            self.context.shadowBlur = shadowBlur
        self.context.drawImage(jqueryImage[0], x, y, w, h)
        self.context.shadowBlur = 0

    @profiler.profile("Canvas.text")
    def text(self, x:float, y:float, text:str, color="black", w=0, font="12px Arial"):
        x = round(x * self.scale + self.offset)
        w = round(w * self.scale) or self.canvas.width()
        self.context.fillStyle = color
        self.context.font = font
        self.context.fillText(text, x, y + 12, w)
        self.maxX = max(self.maxX, x)

    @profiler.profile("Canvas.circle")
    def circle(self, x:float, y:float, radius:float, fill="white", lineWidth=0, color="black"):
        x = round(x * self.scale + self.offset)
        radius = round(radius * self.scale)
        self.context.fillStyle = fill
        self.context.beginPath()
        self.context.arc(x, y, radius, 0, 2 * math.pi)
        self.context.fill()
        if lineWidth:
            self.context.strokeStyle = color
            self.context.lineWidth = lineWidth
            self.context.stroke()
       
    def absolute(self, x:float, w:float):
        return (x - self.offset) / self.scale, w / self.scale
