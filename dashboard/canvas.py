#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import itertools
import json
import js # type: ignore
import math
import pyodide # type: ignore

import dashboard.profiler as profiler
from dashboard import config

jquery = js.jQuery

class Canvas():
    def __init__(self, elementId, redrawCallback, dragCallback=None, zoomCallback=None, clickCallback=None, minOffsetX=0, minOffsetY=0, fixedX=False, fixedY=False, fixedScaleX=False, fixedScaleY=False) -> None:
        self.scaleX = config.CANVAS_INITIAL_SCALE
        self.scaleY = config.CANVAS_INITIAL_SCALE
        self.offsetX = config.CANVAS_INITIAL_OFFSET_X
        self.offsetY = config.CANVAS_INITIAL_OFFSET_Y
        self.redrawCallback = redrawCallback
        self.dragCallback = dragCallback
        self.zoomCallback = zoomCallback
        self.clickCallback = clickCallback
        self.elementId = elementId
        self.minOffsetX = minOffsetX
        self.minOffsetY = minOffsetY
        self.canvas = jquery(elementId)
        self._width = float(self.canvas.attr("width") or js.jQuery("body").width())
        self._height = float(self.canvas.attr("height") or js.jQuery("body").height())
        self.context = self.canvas[0].getContext("2d")
        self.dragX = 0
        self.dragY = 0
        self.dragging = False
        self.mouseDown = False
        self.maxX = 0
        self.fixedX = fixedX
        self.fixedY = fixedY
        self.fixedScaleX = fixedScaleX
        self.fixedScaleY = fixedScaleY
        self.setupEventHandlers()

    def setupEventHandlers(self):
        self.canvas \
            .on("mousedown", pyodide.ffi.create_proxy(lambda event: self.mousedown(event))) \
            .on("mousemove", pyodide.ffi.create_proxy(lambda event: self.mousemove(event))) \
            .on("mouseleave", pyodide.ffi.create_proxy(lambda event: self.mouseleave(event))) \
            .on("mouseup", pyodide.ffi.create_proxy(lambda event: self.mouseup(event))) \
            .on("mousewheel", pyodide.ffi.create_proxy(lambda event: self.mousewheel(event)))

    def mousedown(self, event):
        from dashboard.dialog import dialog
        self.dragX = event.originalEvent.pageX
        self.dragY = event.originalEvent.pageY
        self.hideHighlights()
        self.mouseDown = True
        self.dragging = False

    def isDragging(self):
        return self.dragging

    def mousemove(self, event):
        if self.mouseDown:
            self.dragging = True
            dx = 0 if self.fixedX else event.originalEvent.pageX - self.dragX
            dy = 0 if self.fixedY else event.originalEvent.pageY - self.dragY
            if self.offsetX + dx > self.width() * 0.9:
                dx = 0
            self.dragX = event.originalEvent.pageX
            self.dragY = event.originalEvent.pageY
            if dx < -3 or dx > 3 or dy:
                self.drag(dx, dy, event)
            event.preventDefault()
    
    def drag(self, dx, dy, event=None):
        if not self.fixedX:
            self.offsetX = self.offsetX + dx
        if not self.fixedY:
            self.offsetY = min(0, self.offsetY + dy)
        if event and self.dragCallback:
            self.dragCallback(dx, dy)
            self.redraw()

    def mouseleave(self, event):
        self.dragX = 0
        self.dragY = 0
        self.dragging = False
        self.mouseDown = False

    def mouseup(self, event):
        if self.isDragging():
            self.dragX = 0
            self.dragY = 0
        else:
            if self.offsetY > 0:
                self.offsetY = 0
            self.clickCallback(event.originalEvent.offsetX, event.originalEvent.offsetY)
        self.dragging = False
        self.mouseDown = False

    def hideHighlights(self):
        js.jQuery(".highlight").css("left", 10000)

    def mousewheel(self, event):
        event.preventDefault()
        self.hideHighlights()
        x = event.originalEvent.offsetX
        y = event.originalEvent.offsetY
        self.zoom(x, y, 2 if event.originalEvent.wheelDelta > 0 else 0.5, event)

    def on(self, event, callback):
        self.canvas.on(event, pyodide.ffi.create_proxy(lambda event: callback(event)))
        return self

    def css(self, key, value):
        self.canvas.css(key, value)

    def zoom(self, x, y, scaleFactor, event=None):
        if not self.fixedScaleX:
            self.offsetX = x - (scaleFactor * (x - self.offsetX))
        if not self.fixedScaleY:
            self.offsetY = y - (scaleFactor * (y - self.offsetY))
        self.scaleX = config.CANVAS_INITIAL_SCALE if self.fixedScaleX else scaleFactor * self.scaleX
        self.scaleY = config.CANVAS_INITIAL_SCALE if self.fixedScaleY else scaleFactor * self.scaleY
        if event and self.zoomCallback:
            self.zoomCallback(x, y, scaleFactor)
            self.redraw()
    
    def reset(self):
        self._width = float(self.canvas.attr("width") or js.jQuery("body").width())
        self._height = float(self.canvas.attr("height") or js.jQuery("body").height())
        self.scaleX = self.scaleY = config.CANVAS_INITIAL_SCALE
        self.offsetX = config.CANVAS_INITIAL_OFFSET_X
        self.offsetY = config.CANVAS_INITIAL_OFFSET_Y

    @profiler.profile("Canvas.width")
    def width(self, width=0):
        if width:
            self._width = width
            self.canvas.attr("width", width)
        else:
            return self._width

    def height(self, height=0):
        return self.canvas.attr("height", height) if height else float(self.canvas.attr("height") or 0)

    def toScreenX(self, x):
        return x * self.scaleX + self.offsetX

    def toScreenY(self, y):
        return y * self.scaleY + self.offsetY

    def fromScreenX(self, x):
        return x - self.offsetX / self.scaleX

    def toScreenDimension(self, w):
        return w * self.scaleX

    def fromScreenDimension(self, w):
        return w / self.scaleX

    def setStrokeStyle(self, color):
        self.context.strokeStyle = color

    def setLineWidth(self, lineWidth):
        self.context.lineWidth = lineWidth
    
    def setFont(self, font):
        self.context.font = font

    def setFillStyle(self, fill):
        self.context.fillStyle = fill
    
    def redraw(self, event=None):
        self._width = float(self.canvas.attr("width") or js.jQuery("body").width())
        self._height = float(self.canvas.attr("height") or js.jQuery("body").height())
        self.redrawCallback(event)
        
    @profiler.profile("Canvas.clear")
    def clear(self, color):
        self.setFillStyle(color)
        self.context.fillRect(0, 0, self.width(), self.height())

    @profiler.profile("Canvas.line")
    def line(self, x1:float, y1:float, x2:float, y2:float, lineWidth=1, color="black"):
        x1 = math.ceil(x1 * self.scaleX + self.offsetX)
        x2 = math.ceil(x2 * self.scaleX + self.offsetX)
        y1 = math.ceil(y1 * self.scaleY + self.offsetY)
        y2 = math.ceil(y2 * self.scaleY + self.offsetY)
        self.setStrokeStyle(color)
        self.setLineWidth(lineWidth)
        self.context.beginPath()
        self.context.moveTo(x1, y1)
        self.context.lineTo(x2, y2)
        self.context.stroke()

    @profiler.profile("Canvas.region")
    def region(self, points, fill="white"):
        self.context.beginPath()
        x = math.ceil(points[0][0] * self.scaleX + self.offsetX)
        y = math.ceil(points[0][1] * self.scaleY + self.offsetY)
        self.context.moveTo(x, y)
        for x, y in points[1:]:
            x = math.ceil(x * self.scaleX + self.offsetX)
            y = math.ceil(y * self.scaleY + self.offsetY)
            self.context.lineTo(x, y)
        self.setFillStyle(fill)
        self.context.fill()

    @profiler.profile("Canvas.polygon")
    def polygon(self, points, lineWidth=1, color="black"):
        coordinates = itertools.chain.from_iterable([
            (x * self.scaleX + self.offsetX, y * self.scaleY + self.offsetY)
            for x, y in points
        ])
        return js.optimizedDrawPolygon(self.context, color, lineWidth, json.dumps(list(coordinates)))

    @profiler.profile("Canvas.rects")
    def fillRects(self, rects):
        coordinates = itertools.chain.from_iterable([
            (
                math.ceil(x * self.scaleX + self.offsetX),
                math.ceil(y * self.scaleY + self.offsetY),
                math.ceil(w * self.scaleX),
                math.ceil(h * self.scaleY),
                color
            )
            for x, y, w, h, color in rects
        ])
        return js.optimizedFillRects(self.context, json.dumps(list(coordinates)))

    @profiler.profile("Canvas.lines")
    def lines(self, lines, width, color):
        coordinates = itertools.chain.from_iterable([
            (
                x1 * self.scaleX + self.offsetX,
                y1 * self.scaleY + self.offsetY,
                x2 * self.scaleX + self.offsetX,
                y2 * self.scaleY + self.offsetY,
            )
            for x1, y1, x2, y2, in lines
        ])
        return js.optimizedDrawLines(self.context, width, color, json.dumps(list(coordinates)))

    @profiler.profile("Canvas.texts")
    def texts(self, texts, font):
        coordinates = itertools.chain.from_iterable([
            (
                x * self.scaleX + self.offsetX,
                y * self.scaleY + self.offsetY,
                text,
                color,
                w * self.scaleX,
            )
            for x, y, text, color, w in texts
        ])
        self.setFont(font)
        return js.optimizedDrawTexts(self.context, json.dumps(list(coordinates)))

    @profiler.profile("Canvas.rect")
    def rect(self, x:float, y:float, w:float, h:float, lineWidth=1, color="white"):
        x = math.ceil(x * self.scaleX + self.offsetX)
        y = math.ceil(y * self.scaleY + self.offsetY)
        w = math.ceil(w * self.scaleX)
        h = math.ceil(h * self.scaleY)
        self.setStrokeStyle(color)
        self.setLineWidth(lineWidth)
        self.context.beginPath()
        self.context.rect(x, y, w, h)
        self.context.stroke()

    @profiler.profile("Canvas.fillRect")
    def fillRect(self, x:float, y:float, w:float, h:float, fill="white"):
        x = math.ceil(x * self.scaleX + self.offsetX)
        y = math.ceil(y * self.scaleY + self.offsetY)
        w = math.ceil(w * self.scaleX)
        h = math.ceil(h * self.scaleY)
        self._fillRect(x, y, w, h, fill)

    def _fillRect(self, x:float, y:float, w:float, h:float, fill):
        self.setFillStyle(fill)
        self.context.fillRect(x, y, w, h)

    @profiler.profile("Canvas.image")
    def image(self, x:float, y:float, w:float, h:float, jqueryImage, shadowColor=None, shadowBlur=0):
        x = math.ceil(x * self.scaleX + self.offsetX)
        y = math.ceil(y * self.scaleY + self.offsetY)
        w = math.ceil(w * self.scaleX)
        h = math.ceil(h * self.scaleY)
        if shadowBlur:
            self.context.shadowColor = shadowColor
            self.context.shadowBlur = shadowBlur
        self.context.drawImage(jqueryImage[0], x, y, w, h)
        self.context.shadowBlur = 0

    @profiler.profile("Canvas.text")
    def text(self, x:float, y:float, text:str, color="black", w=0, font="12px Arial"):
        x = math.ceil(x * self.scaleX + self.offsetX)
        y = math.ceil(y * self.scaleY + self.offsetY)
        w = math.ceil(w * self.scaleX) or self.canvas.width()
        self.setFillStyle(color)
        self.setFont(font)
        self.context.fillText(text, x, y + 12, w)
        self.maxX = max(self.maxX, x)

    @profiler.profile("Canvas.circle")
    def circle(self, x:float, y:float, radius:float, fill="white", lineWidth=0, color="black"):
        x = math.ceil(x * self.scaleX + self.offsetX)
        y = math.ceil(y * self.scaleY + self.offsetY)
        radius = math.ceil(radius * self.scaleX)
        self.setFillStyle(fill)
        self.context.beginPath()
        self.context.arc(x, y, radius, 0, 2 * math.pi)
        self.context.fill()
        if lineWidth:
            self.setStrokeStyle(color)
            self.setLineWidth(lineWidth)
            self.context.stroke()
       
    def absolute(self, x:float=0.0, y:float=0.0, w:float=0.0, h:float=0.0):
        return (
            (x - self.offsetX) / self.scaleX,
            (y - self.offsetY) / self.scaleY,
            w / self.scaleX,
            h / self.scaleY,
        )
