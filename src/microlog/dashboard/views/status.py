#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""A visual representation of system status samples in the Microlog dashboard."""

from __future__ import annotations

from typing import Callable
from typing import Sequence

import ltk

from microlog.dashboard import config
from microlog.dashboard.canvas import Canvas
from microlog.dashboard.views import View
from microlog.models import Status
from microlog.models import to_gb


class StatusView(View):
    """A visual representation of a system status sample in the dashboard."""

    instances: list["StatusView"] = []
    last_when: float = 0.0

    def __init__(self, canvas: Canvas, model: Status) -> None:
        """Initialize a StatusView instance."""
        self.model: Status = model
        View.__init__(self, canvas)
        self.h: float = config.STATS_HEIGHT
        self.previous: StatusView | None = None
        StatusView.instances.append(self)
        StatusView.last_when = max(model.when, StatusView.last_when)

    @classmethod
    def reset(cls) -> None:
        """Reset all StatusView instances and hide the summary."""
        StatusView.instances.clear()
        ltk.find("#summary").css("display", "none")

    def inside(self, x: float, y: float) -> bool:
        """Return True if the given coordinates are inside this status area."""
        if not self.previous:
            return False
        return (
            x >= self.previous.x and x < self.x and y >= self.y and y < self.y + self.h
        )

    @classmethod
    def draw_all(cls, canvas: Canvas, views: list["StatusView"]) -> None:
        """Draw all status views on the canvas."""
        if views:
            canvas.clear("#222")
            query = ltk.find(".span-search").val().lower()
            cls.draw_cpu(canvas, views, query)
            cls.draw_memory(canvas, views, query)
            cls.draw_modules(canvas, views, query)
            cls.draw_object_counts(canvas, views, query)
            previous = None
            for view in views:
                view.previous = previous
                previous = view

    @classmethod
    def draw_modules(
        cls, canvas: Canvas, views: list["StatusView"], query: str
    ) -> None:
        """Draw the modules count polygon on the canvas."""
        max_module_count = max(view.module_count for view in views)
        points = cls.get_points(
            views, lambda status: status.module_count, max_module_count, 20
        )
        canvas.polygon(points, 2, "#555" if query else "#f6ff00AA")

    @classmethod
    def draw_memory(
        cls, canvas: Canvas, views: list["StatusView"], query: str
    ) -> None:
        """Draw the memory usage polygon on the canvas."""
        max_memory = max(view.memory for view in views)
        points = cls.get_points(views, lambda status: status.memory, max_memory, 10)
        canvas.polygon(points, 3, "#555" if query else "#DD0000AA")

    @classmethod
    def draw_cpu(
        cls, canvas: Canvas, views: list["StatusView"], query: str
    ) -> None:
        """Draw the CPU usage polygon on the canvas."""
        line_points = cls.get_points(
            views, lambda status: 1.1 * (status.cpu - 10), 100, 5
        )
        canvas.polygon(line_points, 1, "#555" if query else "#549f56")

    @classmethod
    def draw_object_counts(
        cls, canvas: Canvas, views: Sequence["StatusView"], query: str
    ) -> None:
        """Draw the object count polygon on the canvas."""
        max_object_count = 2 * max(view.object_count for view in views)
        line_points = cls.get_points(
            views, lambda status: status.object_count, max_object_count, 5
        )
        canvas.polygon(line_points, 1, "#555" if query else "#f8f8f8")

    @classmethod
    def get_points(
        cls,
        views: Sequence["StatusView"],
        get_value: Callable[["StatusView"], float],
        max_value: float,
        offset: int,
    ) -> Sequence[tuple[int, int]]:
        """Calculate polygon points for a given metric."""
        height = config.STATS_HEIGHT
        max_y = config.STATS_OFFSET_Y + config.STATS_HEIGHT
        points: list[tuple[int, int]] = []
        for status in views:
            x = round(status.x)
            y = round(max_y - get_value(status) * (height - offset * 2) / (max_value + 1) - 5)
            if len(points) > 2 and points[-1][1] == points[-2][1] == y:
                points.pop()
            points.append((x, y))
        return points

    @classmethod
    def get_status_at(cls, when: float) -> "StatusView" | None:
        """Get the StatusView instance closest to the given time."""
        previous = None
        for view in cls.instances:
            status = view.model
            if status.when > when:
                return previous or view
            previous = view
        return None

    def offscreen(self, scale_x: float, offset_x: float, width: float) -> bool:
        """Return True if this status is offscreen given the current scale and offset."""
        x = self.x * scale_x + offset_x
        w = self.w * scale_x
        offset = scale_x * width / 2
        return x + w < -offset or x > width + offset

    def mousemove(self, x: float, y: float) -> None:
        """Handle mouse movement over this status view."""
        if not self.previous:
            return
        self.show_hairline(x)
        cpu = (self.previous.cpu + self.cpu) / 2 if self.previous else self.cpu
        html = f"""
            T={self.previous.when:.1f}s<br>
            <span style="color:#549f56">CPU={round(cpu)}%</span><br>
            <span style="color:#f6ff00AA">Modules={self.module_count:,}</span><br>
            <span style="color:#f06161aa">Memory={to_gb(self.memory)}</span><br>
            <span style="color:white">Objects={self.object_count:,}</span><br>
        """
        ltk.find("#summary").css("display", "block").html(html)

    def show_hairline(self, x: float) -> None:
        """Show a vertical hairline indicator at the given x position."""
        position = ltk.find("#flameCanvas").position()
        (ltk.find("#hairline")
            .css("display", "block")
            .css("top", 1)
            .css("left", position.left + self.canvas.to_screen_x(x) - 7)
            .css("height", config.STATS_HEIGHT))

    def __str__(self) -> str:
        """Return a string representation of the status view."""
        return f"cpu: {round(self.cpu)}%, memory: {to_gb(self.memory)}, " \
            f"modules: {round(self.module_count)}, objects: {round(self.object_count)}"
