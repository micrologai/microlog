#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Timeline visualization for the dashboard."""

from __future__ import annotations

from typing import Callable

from microlog.dashboard import config
from microlog.dashboard.canvas import Canvas
from microlog.dashboard.views import status


class Timeline:
    """Timeline visualization for the dashboard."""

    def draw(self, canvas: Canvas) -> None:
        """Draw the timeline on the canvas."""
        self.clear(canvas)
        self.draw_ticks(canvas)

    def draw_ticks(self, canvas: Canvas) -> None:
        """Draw tick marks and labels on the timeline."""
        y = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT
        h = canvas.height()
        lines = []
        ticks = []
        texts = []
        tick = self.get_tick(canvas)

        def add_tick(n: int, x: float) -> None:
            """Add a tick mark and label at position x."""
            second = n * tick
            ticks.append((x, y - 13, x, h))
            label = (
                f"{second:0.2f}s"
                if tick < 0.1
                else f"{second:0.1f}s"
                if tick < 1
                else f"{second:0.0f}s"
            )
            cx = x - canvas.from_screen_dimension(len(label) * config.FONT_SIZE_SMALL / 4)
            texts.append(
                (
                    cx,
                    config.TIMELINE_OFFSET_Y + 23,
                    label,
                    "gray",
                    canvas.from_screen_dimension(100),
                )
            )
            lines.append((x, 0, x, config.TIMELINE_OFFSET_Y))

        self.draw_visible_seconds(canvas, add_tick)
        canvas.lines(ticks, 1, "gray")
        canvas.lines(lines, 1, "gray")
        canvas.texts(texts, config.FONT_SMALL)

    def get_tick(self, canvas: Canvas) -> float:
        """Determine the appropriate tick interval based on the canvas scale."""
        scale_x = canvas.scale_x
        return (
            0.01
            if scale_x > 128
            else 0.1
            if scale_x > 4
            else 1000.0
            if scale_x < 0.00390625
            else 100.0
            if scale_x < 0.0625
            else 10.0
            if scale_x < 0.5
            else 1.0
        )

    def draw_visible_seconds(
        self, canvas: Canvas, draw: Callable[[int, float], None]
    ) -> None:
        """Draw ticks for all visible seconds on the canvas."""
        tick = self.get_tick(canvas)
        for n in range(0, int(status.StatusView.last_when) + 1):
            second = n * tick
            x = second * config.PIXELS_PER_SECOND
            if x < 0:
                continue
            draw(n, x)
            if canvas.to_screen_x(x) >= canvas.width():
                break

    def clear(self, canvas: Canvas) -> None:
        """Clear the timeline area on the canvas."""
        x, _, w, _ = canvas.absolute(0, 0, canvas.width())
        y = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT
        canvas.fill_rect(x, config.TIMELINE_OFFSET_Y, w, config.TIMELINE_HEIGHT, "white")
        canvas.line(x, y, x + w, y, 3, "gray")
