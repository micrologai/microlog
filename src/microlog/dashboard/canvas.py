#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Canvas abstraction for drawing dashboard visualizations."""

from __future__ import annotations

import itertools
import json
import math
import time
from typing import Any
from typing import Callable
from typing import Sequence
from typing import Union

import ltk
import js
from microlog.dashboard import config


class Canvas:
    """Canvas abstraction for drawing dashboard visualizations."""

    def __init__(
        self,
        element_id: str,
        redraw_callback: Callable[..., Any],
        drag_callback: Callable[[float, float], None] | None = None,
        zoom_callback: Callable[[float, float, float], None] | None = None,
        click_callback: Callable[[float, float], None] | None = None,
        min_offset_x: float = 0,
        min_offset_y: float = 0,
        fixed_x: bool = False,
        fixed_y: bool = False,
        fixed_scale_x: bool = False,
        fixed_scale_y: bool = False,
    ) -> None:
        """Initialize a Canvas instance."""
        self.scale_x = config.CANVAS_INITIAL_SCALE / 3
        self.scale_y = config.CANVAS_INITIAL_SCALE
        self.offset_x: float = float(config.CANVAS_INITIAL_OFFSET_X)
        self.offset_y: float = float(config.CANVAS_INITIAL_OFFSET_Y)

        self.redraw_callback = redraw_callback
        self.drag_callback = drag_callback
        self.zoom_callback = zoom_callback
        self.click_callback = click_callback

        self.element_id = element_id
        self.min_offset_x = min_offset_x
        self.min_offset_y = min_offset_y

        self.canvas = ltk.find(element_id)
        self._width = float(
            js.parseFloat(self.canvas.attr("width")) or ltk.find("body").width()
        )
        self._height = float(
            js.parseFloat(self.canvas.attr("height")) or ltk.find("body").height()
        )
        self.context = self.canvas[0].getContext("2d")
        self.drag_x = 0
        self.drag_y = 0
        self.dragging = False
        self.mouse_down = False
        self.max_x = 0
        self.fixed_x = fixed_x
        self.fixed_y = fixed_y
        self.fixed_scale_x = fixed_scale_x
        self.fixed_scale_y = fixed_scale_y
        self.setup_event_handlers()
        self.last_wheel_event = 0

    def setup_event_handlers(self) -> None:
        """Set up mouse and keyboard event handlers for the canvas."""
        self.canvas.on(
            "mousedown", 
            ltk.proxy(lambda event: self.mousedown(event)) # pylint: disable=unnecessary-lambda
        ).on(
            "mousemove", 
            ltk.proxy(lambda event: self.mousemove(event)) # pylint: disable=unnecessary-lambda
        ).on(
            "mouseleave", 
            ltk.proxy(lambda event: self.mouseleave(event)) # pylint: disable=unnecessary-lambda
        ).on(
            "mouseup", 
            ltk.proxy(lambda event: self.mouseup(event)) # pylint: disable=unnecessary-lambda
        ).on(
            "mousewheel", 
            ltk.proxy(lambda event: self.canvas_mousewheel(event)) # pylint: disable=unnecessary-lambda
        )
        ltk.find("body").on(
            "keydown", ltk.proxy(lambda event: self.keydown(event)) # pylint: disable=unnecessary-lambda
        )

    def mousedown(self, event: Any) -> None:
        """Handle mouse down event."""
        self.drag_x = event.originalEvent.pageX
        self.drag_y = event.originalEvent.pageY
        self.mouse_down = True
        self.dragging = False

    def is_dragging(self) -> bool:
        """Return True if the canvas is currently being dragged."""
        return self.dragging

    def mousemove(self, event: Any) -> None:
        """Handle mouse move event."""
        if self.mouse_down:
            self.dragging = True
            dx = 0 if self.fixed_x else event.originalEvent.pageX - self.drag_x
            dy = 0 if self.fixed_y else event.originalEvent.pageY - self.drag_y
            if self.offset_x + dx > self.width() * 0.9:
                dx = 0
            self.drag_x = event.originalEvent.pageX
            self.drag_y = event.originalEvent.pageY
            if dx < -3 or dx > 3 or dy:
                self.drag(dx, dy, event)
            event.preventDefault()

    def drag(self, dx: float, dy: float, event: Any | None = None) -> None:
        """Handle drag event and update offsets."""
        if not self.fixed_x:
            self.offset_x = self.offset_x + dx
        if not self.fixed_y:
            self.offset_y = min(0, self.offset_y + dy)
        if event and self.drag_callback:
            self.drag_callback(dx, dy)
            self.redraw()

    def mouseleave(self, _event: Any) -> None:
        """Handle mouse leave event."""
        self.drag_x = 0
        self.drag_y = 0
        self.dragging = False
        self.mouse_down = False

    def keydown(self, event: Any) -> None:
        """Handle key down event for zoom and reset."""
        if getattr(event.originalEvent, "shiftKey", None):
            return None
        if getattr(event.originalEvent, "metaKey", None) or getattr(
            event.originalEvent, "ctrlKey", None
        ):
            if event.key == "0":
                self.offset_x = 48.0
                self.zoom(0, 0, config.CANVAS_INITIAL_SCALE)
            elif event.key == "-":
                self.offset_x = 48.0
                self.zoom(0, 0, config.ZOOM_OUT_FACTOR, event)
            elif event.key in ("=", "+"):
                self.offset_x = 0.0
                self.zoom(0, 0, config.ZOOM_IN_FACTOR, event)
            else:
                return None
            event.preventDefault()
            event.stopPropagation()

    def mouseup(self, event: Any) -> None:
        """Handle mouse up event."""
        if self.is_dragging():
            self.drag_x = 0
            self.drag_y = 0
        else:
            if self.offset_y > 0:
                self.offset_y = 0.0
            if self.click_callback:
                self.click_callback(
                    event.originalEvent.offsetX, event.originalEvent.offsetY
                )
        self.dragging = False
        self.mouse_down = False

    def canvas_mousewheel(self, event: Any) -> None:
        """Handle mouse wheel event in the main canvas."""
        self.wheel_zoom(
            event.originalEvent.offsetX,
            event.originalEvent.offsetY,
            event
        )

    def wheel_zoom(self, x: float, y: float, event: Any) -> None:
        """Use the wheel event to zoom"""
        if time.time() - self.last_wheel_event < 0.1:
            return
        self.last_wheel_event = time.time()
        event.preventDefault()
        wheel = event.originalEvent.wheelDelta > 0
        zoom_factor = config.ZOOM_IN_FACTOR if wheel else config.ZOOM_OUT_FACTOR
        self.zoom(x, y, zoom_factor, event)

    def on(self, event: str, callback: Callable[[Any], Any]) -> "Canvas":
        """Attach an event handler to the canvas."""
        self.canvas.on(event, ltk.proxy(lambda event: callback(event))) # pylint: disable=unnecessary-lambda
        return self

    def css(self, key: str, value: Union[str,float]) -> Canvas:
        """Set a CSS property on the canvas."""
        self.canvas.css(key, value)
        return self

    def zoom(
        self,
        x: float,
        y: float,
        scale_factor: float,
        event: Any | None = None
    ) -> None:
        """Zoom the canvas view."""
        if not self.fixed_scale_x:
            self.offset_x = x - (scale_factor * (x - self.offset_x))
        if not self.fixed_scale_y:
            self.offset_y = y - (scale_factor * (y - self.offset_y))
        self.scale_x = max(
            config.MIN_ZOOM_FACTOR,
            config.CANVAS_INITIAL_SCALE
            if self.fixed_scale_x
            else scale_factor * self.scale_x,
        )
        self.scale_y = max(
            config.MIN_ZOOM_FACTOR,
            config.CANVAS_INITIAL_SCALE
            if self.fixed_scale_y
            else scale_factor * self.scale_y,
        )
        if event and self.zoom_callback:
            self.zoom_callback(x, y, scale_factor)
            self.redraw()

    def reset(self) -> None:
        """Reset the canvas to its initial state."""
        self._width = float(self.canvas.attr("width") or ltk.find("body").width())
        self._height = float(self.canvas.attr("height") or ltk.find("body").height())
        self.scale_x = self.scale_y = config.CANVAS_INITIAL_SCALE
        self.offset_x = float(config.CANVAS_INITIAL_OFFSET_X)
        self.offset_y = float(config.CANVAS_INITIAL_OFFSET_Y)

    def width(self, width: float = 0) -> float:
        """Get or set the canvas width."""
        if width:
            self._width = width
            self.canvas.attr("width", width)
            return width
        else:
            return js.parseFloat(self.canvas.attr("width") or 0)

    def height(self, height: float = 0) -> float:
        """Get or set the canvas height."""
        if height:
            self.canvas.attr("height", height)
            return height
        else:
            return js.parseFloat(self.canvas.attr("height") or 0)

    def to_screen_x(self, x: float) -> float:
        """Convert logical x to screen x."""
        return x * self.scale_x + self.offset_x

    def to_screen_y(self, y: float) -> float:
        """Convert logical y to screen y."""
        return y * self.scale_y + self.offset_y

    def from_screen_x(self, x: float) -> float:
        """Convert screen x to logical x."""
        return x - self.offset_x / self.scale_x

    def to_screen_dimension(self, w: float) -> float:
        """Convert logical width to screen width."""
        return w * self.scale_x

    def from_screen_dimension(self, w: float) -> float:
        """Convert screen width to logical width."""
        return w / self.scale_x

    def set_stroke_style(self, color: str) -> None:
        """Set the stroke color for drawing."""
        self.context.strokeStyle = color

    def set_line_width(self, line_width: float) -> None:
        """Set the line width for drawing."""
        self.context.lineWidth = line_width

    def set_font(self, font: str) -> None:
        """Set the font for text drawing."""
        self.context.font = font

    def set_fill_style(self, fill: str) -> None:
        """Set the fill color for drawing."""
        self.context.fillStyle = fill

    def redraw(self, event: Any | None = None) -> None:
        """Redraw the canvas using the redraw callback."""
        self._width = float(self.canvas.attr("width") or ltk.find("body").width())
        self._height = float(self.canvas.attr("height") or ltk.find("body").height())
        self.redraw_callback(event)

    def clear(self, color: str) -> None:
        """Clear the canvas with the given color."""
        self.set_fill_style(color)
        self.context.fillRect(0, 0, int(self.width() or 0), int(self.height() or 0))

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        line_width: float = 1,
        color: str = "black",
    ) -> None:
        """Draw a line on the canvas."""
        x1 = math.ceil(x1 * self.scale_x + self.offset_x)
        x2 = math.ceil(x2 * self.scale_x + self.offset_x)
        y1 = math.ceil(y1 * self.scale_y + self.offset_y)
        y2 = math.ceil(y2 * self.scale_y + self.offset_y)
        self.set_stroke_style(color)
        self.set_line_width(line_width)
        self.context.beginPath()
        self.context.moveTo(x1, y1)
        self.context.lineTo(x2, y2)
        self.context.stroke()

    def region(self, points: list[tuple[float, float]], fill: str = "white") -> None:
        """Draw a filled region defined by points."""
        self.context.beginPath()
        x = math.ceil(points[0][0] * self.scale_x + self.offset_x)
        y = math.ceil(points[0][1] * self.scale_y + self.offset_y)
        self.context.moveTo(x, y)
        for px, py in points[1:]:
            x = math.ceil(px * self.scale_x + self.offset_x)
            y = math.ceil(py * self.scale_y + self.offset_y)
            self.context.lineTo(x, y)
        self.set_fill_style(fill)
        self.context.fill()

    def polygon(
        self,
        points: Sequence[tuple[float, float]],
        line_width: float = 1,
        color: str = "black",
    ) -> Any:
        """Draw a polygon on the canvas."""
        coordinates = itertools.chain(
            *[
                (x * self.scale_x + self.offset_x, y * self.scale_y + self.offset_y)
                for x, y in points
            ]
        )
        return js.optimizedDrawPolygon(
            self.context, color, line_width, json.dumps(list(coordinates))
        )

    def fill_rects(self, rects: Any) -> Any:
        """Draw multiple filled rectangles on the canvas."""
        coordinates = itertools.chain(
            *[
                (
                    math.ceil(x * self.scale_x + self.offset_x),
                    math.ceil(y * self.scale_y + self.offset_y),
                    math.ceil(w * self.scale_x),
                    math.ceil(h * self.scale_y),
                    color,
                )
                for x, y, w, h, color in rects
            ]
        )
        return js.optimizedFillRects(self.context, json.dumps(list(coordinates)))

    def lines(self, lines: Any, width: float, color: str) -> Any:
        """Draw multiple lines on the canvas."""
        coordinates = itertools.chain(
            *[
                (
                    x1 * self.scale_x + self.offset_x,
                    y1 * self.scale_y + self.offset_y,
                    x2 * self.scale_x + self.offset_x,
                    y2 * self.scale_y + self.offset_y,
                )
                for x1, y1, x2, y2 in lines
            ]
        )
        return js.optimizedDrawLines(
            self.context, width, color, json.dumps(list(coordinates))
        )

    def texts(self, texts: Any, font: str) -> Any:
        """Draw multiple texts on the canvas."""
        coordinates = itertools.chain(
            *[
                (
                    x * self.scale_x + self.offset_x,
                    y * self.scale_y + self.offset_y,
                    text,
                    color,
                    w * self.scale_x,
                )
                for x, y, text, color, w in texts
            ]
        )
        self.set_font(font)
        return js.optimizedDrawTexts(self.context, json.dumps(list(coordinates)))

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        line_width: float = 1,
        color: str = "white",
    ) -> None:
        """Draw a rectangle on the canvas."""
        x = math.ceil(x * self.scale_x + self.offset_x)
        y = math.ceil(y * self.scale_y + self.offset_y)
        w = math.ceil(w * self.scale_x)
        h = math.ceil(h * self.scale_y)
        self.set_stroke_style(color)
        self.set_line_width(line_width)
        self.context.beginPath()
        self.context.rect(x, y, w, h)
        self.context.stroke()

    def fill_rect(
        self, x: float, y: float, w: float, h: float, fill: str = "white"
    ) -> None:
        """Draw a filled rectangle on the canvas."""
        x = math.ceil(x * self.scale_x + self.offset_x)
        y = math.ceil(y * self.scale_y + self.offset_y)
        w = math.ceil(w * self.scale_x)
        h = math.ceil(h * self.scale_y)
        self._fill_rect(x, y, w, h, fill)

    def _fill_rect(self, x: float, y: float, w: float, h: float, fill: str) -> None:
        """Internal method to fill a rectangle."""
        self.set_fill_style(fill)
        self.context.fillRect(x, y, w, h)

    def image(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        jquery_image: Any,
        shadow_color: str | None = None,
        shadow_blur: float = 0,
    ) -> None:
        """Draw an image on the canvas."""
        if not jquery_image:
            js.console.log("Cannot draw missing image")
            return
        x = math.ceil(x * self.scale_x + self.offset_x)
        y = math.ceil(y * self.scale_y + self.offset_y)
        w = math.ceil(w * self.scale_x)
        h = math.ceil(h * self.scale_y)
        if shadow_blur:
            self.context.shadowColor = shadow_color
            self.context.shadowBlur = shadow_blur
        self.context.drawImage(jquery_image[0], x, y, w, h)
        self.context.shadowBlur = 0

    def text(
        self,
        x: float,
        y: float,
        text: str,
        color: str = "black",
        w: float = 0,
        font: str = "12px Arial",
    ) -> None:
        """Draw text on the canvas."""
        x = math.ceil(x * self.scale_x + self.offset_x)
        y = math.ceil(y * self.scale_y + self.offset_y)
        w = math.ceil(w * self.scale_x) or self.canvas.width()
        self.set_fill_style(color)
        self.set_font(font)
        self.context.fillText(text, x, y + 12, w)
        self.max_x = max(self.max_x, x)

    def circle(
        self,
        x: float,
        y: float,
        radius: float,
        fill: str = "white",
        line_width: float = 0,
        color: str = "black",
    ) -> None:
        """Draw a circle on the canvas."""
        x = math.ceil(x * self.scale_x + self.offset_x)
        y = math.ceil(y * self.scale_y + self.offset_y)
        radius = math.ceil(radius * self.scale_x)
        js.circle(self.context, x, y, radius, fill, line_width, color)

    def absolute(
        self, x: float = 0.0, y: float = 0.0, w: float = 0.0, h: float = 0.0
    ) -> tuple[float, float, float, float]:
        """Convert screen coordinates to logical coordinates."""
        return (
            (x - self.offset_x) / self.scale_x,
            (y - self.offset_y) / self.scale_y,
            w / self.scale_x,
            h / self.scale_y,
        )
