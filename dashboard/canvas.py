#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import itertools
import math
import js # type: ignore
import pyodide # type: ignore

import dashboard.profiler as profiler

jquery = js.jQuery

class Canvas():
    def __init__(self, elementId, redrawCallback) -> None:
        self.scale = 1
        self.offset = 24
        self.redrawCallback = redrawCallback
        self.canvas = jquery(elementId)
        self.context = self.canvas[0].getContext("2d")
        self.dragX = 0
        self.maxX = 0
        self.fill = None
        self.font = None
        self.color = None
        self.lineWidth = None
        self._width = self.canvas.parent().width()
        self._height = self.canvas.parent().height()
        self.setupEventHandlers()

    def setupEventHandlers(self):
        jquery(js.window).on("resize", pyodide.ffi.create_proxy(lambda event: self.redraw()))
        self.canvas \
            .on("mousedown", pyodide.ffi.create_proxy(lambda event: self.mousedown(event))) \
            .on("mousemove", pyodide.ffi.create_proxy(lambda event: self.mousemove(event))) \
            .on("mouseleave", pyodide.ffi.create_proxy(lambda event: self.mouseleave(event))) \
            .on("mouseup", pyodide.ffi.create_proxy(lambda event: self.mouseup(event))) \
            .on("mousewheel", pyodide.ffi.create_proxy(lambda event: self.mousewheel(event)))

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
                if dx < -3 or dx > 3:
                    self.drag(dx, event)
            event.preventDefault()
    
    def drag(self, dx, event):
        self.offset += dx
        self.redraw()

    def mouseleave(self, event):
        self.dragX = 0

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
        from dashboard.views import config
        newScale = scaleFactor * self.scale
        if scaleFactor < 1 and newScale >= config.SCALE_MIN or scaleFactor > 1 and newScale <= config.SCALE_MAX:
            self.offset = x - (scaleFactor * (x - self.offset))
            self.scale = newScale
            self.redraw()
    
    def reset(self):
        self.scale = 1
        self.offset = 24

    def width(self):
        return self._width

    def height(self):
        return self._height

    def toScreenX(self, x):
        assert isinstance(x, (int, float)), f"x should be a number, not {type(x)}: {x}"
        return x * self.scale + self.offset

    def fromScreenX(self, x):
        return x - self.offset / self.scale

    def toScreenDimension(self, w):
        return w * self.scale

    def fromScreenDimension(self, w):
        return w / self.scale

    def setStrokeStyle(self, color):
        if self.color != color:
            self.context.strokeStyle = self.color = color

    def setLineWidth(self, lineWidth):
        if self.lineWidth != lineWidth:
            self.context.lineWidth = self.lineWidth = lineWidth
    
    def setFont(self, font):
        if self.font != font:
            self.context.font = self.font = font

    def setFillStyle(self, fill):
        if self.fill != fill:
            self.context.fillStyle = self.fill = fill
    
    def setFont(self, font):
        if self.font != font:
            self.context.font = self.font = font

    def redraw(self, event=None):
        self.redrawCallback(event)
        
    def resize(self):
        self._width = self.canvas.parent().width()
        self._height = self.canvas.parent().height()
        if self._width and self._height:
            self.canvas.attr("width", self._width).attr("height", self._height)
        
    def clear(self, color):
        self.resize()
        x, w = self.absolute(0, self.width())
        h = self.height()
        self.fillRect(x, 0, w, h, color)

    @profiler.profile("Canvas.line")
    def line(self, x1:float, y1:float, x2:float, y2:float, lineWidth=1, color="black"):
        x1 = math.ceil(x1 * self.scale + self.offset)
        x2 = math.ceil(x2 * self.scale + self.offset)
        self.setStrokeStyle(color)
        self.setLineWidth(lineWidth)
        self.context.beginPath()
        self.context.moveTo(x1, y1)
        self.context.lineTo(x2, y2)
        self.context.stroke()

    @profiler.profile("Canvas.region")
    def region(self, points, fill="white"):
        self.context.beginPath()
        self.context.moveTo(math.ceil(points[0][0] * self.scale + self.offset), points[0][1])
        for x, y in points[1:]:
            x = math.ceil(x * self.scale + self.offset)
            self.context.lineTo(x, y)
        self.setFillStyle(fill)
        self.context.fill()

    @profiler.profile("Canvas.polygon")
    def polygon(self, points, lineWidth=1, color="black"):
        coordinates = itertools.chain.from_iterable([
            (x * self.scale + self.offset, y)
            for x, y in points
        ])
        return js.optimizedDrawPolygon(self.context, lineWidth, color, *coordinates)

    @profiler.profile("Canvas.rects")
    def fillRects(self, rects):
        coordinates = itertools.chain.from_iterable([
            (
                math.ceil(x * self.scale + self.offset),
                y, 
                math.ceil(w * self.scale),
                h,
                color
            )
            for x, y, w, h, color in rects
        ])
        return js.optimizedFillRects(self.context, *coordinates)

    @profiler.profile("Canvas.lines")
    def lines(self, lines, width, color):
        coordinates = itertools.chain.from_iterable([
            (
                x1 * self.scale + self.offset,
                y1,
                x2 * self.scale + self.offset,
                y2,
            )
            for x1, y1, x2, y2, in lines
        ])
        return js.optimizedDrawLines(self.context, width, color, *coordinates)

    @profiler.profile("Canvas.texts")
    def texts(self, texts, font):
        coordinates = itertools.chain.from_iterable([
            (
                x * self.scale + self.offset,
                y,
                text,
                color,
                w * self.scale,
            )
            for x, y, text, color, w in texts
        ])
        self.setFont(font)
        return js.optimizedDrawTexts(self.context, *coordinates)

    @profiler.profile("Canvas.rect")
    def rect(self, x:float, y:float, w:float, h:float, lineWidth=1, color="white"):
        x = math.ceil(x * self.scale + self.offset)
        w = math.ceil(w * self.scale)
        self.setStrokeStyle(color)
        self.setLineWidth(lineWidth)
        self.context.beginPath()
        self.context.rect(x, y, w, h)
        self.context.stroke()

    @profiler.profile("Canvas.fillRect")
    def fillRect(self, x:float, y:float, w:float, h:float, fill="white"):
        x = math.ceil(x * self.scale + self.offset)
        w = math.ceil(w * self.scale)
        self.setFillStyle(fill)
        self.context.fillRect(x, y, w, h)

    @profiler.profile("Canvas.image")
    def image(self, x:float, y:float, w:float, h:float, jqueryImage, shadowColor=None, shadowBlur=0):
        x = math.ceil(x * self.scale + self.offset)
        w = math.ceil(w * self.scale)
        h = math.ceil(h)
        if shadowBlur:
            self.context.shadowColor = shadowColor
            self.context.shadowBlur = shadowBlur
        self.context.drawImage(jqueryImage[0], x, y, w, h)
        self.context.shadowBlur = 0

    @profiler.profile("Canvas.text")
    def text(self, x:float, y:float, text:str, color="black", w=0, font="12px Arial"):
        x = math.ceil(x * self.scale + self.offset)
        w = math.ceil(w * self.scale) or self.canvas.width()
        self.setFillStyle(color)
        self.setFont(font)
        self.context.fillText(text, x, y + 12, w)
        self.maxX = max(self.maxX, x)

    @profiler.profile("Canvas.circle")
    def circle(self, x:float, y:float, radius:float, fill="white", lineWidth=0, color="black"):
        x = math.ceil(x * self.scale + self.offset)
        radius = math.ceil(radius * self.scale)
        self.setFillStyle(fill)
        self.context.beginPath()
        self.context.arc(x, y, radius, 0, 2 * math.pi)
        self.context.fill()
        if lineWidth:
            self.setStrokeStyle(color)
            self.setLineWidth(lineWidth)
            self.context.stroke()
       
    def absolute(self, x:float, w:float):
        return (x - self.offset) / self.scale, w / self.scale
