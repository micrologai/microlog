"""Manages the flamegraph and timeline visualizations."""

from typing import Any
from typing import Callable

import ltk
import js

from microlog.dashboard import config
from microlog.dashboard import markdown
from microlog.dashboard.colors import colorize
from microlog.dashboard.canvas import Canvas
from microlog.dashboard.dialog import dialog
from microlog.dashboard.views import timeline
from microlog.dashboard.views.call import CallView
from microlog.dashboard.views.marker import MarkerView
from microlog.dashboard.views.status import StatusView
from microlog.models import recording


class Flamegraph:
    """Manages the flamegraph and timeline visualizations."""
    def __init__(self, flame_element_id: str, timeline_element_id: str) -> None:
        self.timeline_element_id = timeline_element_id
        self.flame_element_id = flame_element_id
        self.timeline = timeline.Timeline()
        self.hover = None
        self.calls: list[CallView] = []
        self.statuses: list[StatusView] = []
        self.markers: list[MarkerView] = []
        self.stacks: dict[int, str] = {}
        self.timeline_canvas: Canvas = self.create_canvas(
            self.timeline_element_id,
            0,
            self.draw_timeline,
            self.click_timeline,
            self.drag_timeline,
            self.zoom_timeline,
            self.timeline_mousemove,
            fixed_y=True,
            fixed_scale_y=True
        )
        self.flame_canvas: Canvas = self.create_canvas(
            self.flame_element_id,
            182,
            self.draw_flame,
            self.click_flame,
            self.drag_flame,
            self.zoom_flame,
            self.flame_mousemove,
            fixed_scale_y=True
        )

    def drag_flame(self, dx: float, dy: float) -> None:
        """Handle drag events on the flame canvas."""
        self.timeline_canvas.drag(dx, dy)
        CallView.position_threads(self.flame_canvas)
        self.draw_timeline()

    def zoom_flame(self, x: float, y: float, scale: float) -> None:
        """Handle zoom events on the flame canvas."""
        self.timeline_canvas.zoom(x, y, scale)
        self.draw_timeline()

    def drag_timeline(self, dx: float, dy: float) -> None:
        """Handle drag events on the timeline canvas."""
        self.flame_canvas.drag(dx, dy)
        self.draw_flame()

    def zoom_timeline(self, x: float, y: float, scale: float) -> None:
        """Handle zoom events on the timeline canvas."""
        self.flame_canvas.zoom(x, y, scale)
        self.draw_flame()

    def create_canvas(
        self,
        element_id: str,
        top: float,
        redraw: Callable[..., Any],
        click: Callable[[float, float], Any],
        drag: Callable[[float, float], None],
        zoom: Callable[[float, float, float], None],
        mousemove: Callable[[Any], None],
        fixed_y: bool = False,
        fixed_scale_y: bool = False,
    ) -> Any:
        """Create and configure a Canvas object for drawing."""
        return (
            Canvas(
                element_id,
                redraw,
                drag,
                zoom,
                click,
                min_offset_x=48,
                min_offset_y=0,
                fixed_y=fixed_y,
                fixed_scale_y=fixed_scale_y,
            )
            .on("mousemove", mousemove)
            .css("position", "absolute")
            .css("top", top)
            .css("cursor", "pointer")
        )

    def resize(self) -> None:
        """Resize the flamegraph and timeline canvases."""
        width = ltk.find("body").width() - 2
        height = ltk.find("body").height() - 2

        timeline_height = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT
        self.timeline_canvas.width(width)
        self.timeline_canvas.height(timeline_height)

        new_width = width - 8
        new_height = height - timeline_height - config.tabs_height() - 2

        self.flame_canvas.width(new_width)
        self.flame_canvas.height(new_height)
        ltk.find(".tabs-panel").width(new_width).height(new_height)

        self.draw()

    def clear(self, canvas: Any | None = None) -> None:
        """Clear the canvases and hide dialogs."""
        if canvas:
            canvas.clear("#222")
        else:
            self.flame_canvas.clear("#222")
            self.timeline_canvas.clear("#222")
        dialog.hide()
        CallView.selected = None
        js.jQuery(".highlight").css("left", 10000)

    def draw_timeline(self, _event: Any | None = None) -> None:
        """Draw the timeline and associated statuses and markers."""
        self.clear(self.timeline_canvas)
        js.jQuery("#hairline").css("display", "none")
        self.hover = None
        self.draw_statuses()
        self.draw_markers()
        if self.markers:
            self.timeline.draw(self.timeline_canvas)

    def draw_statuses(self) -> None:
        """Draw the status views on the timeline canvas."""
        canvas_scale_x = self.flame_canvas.scale_x
        canvas_offset_x = self.flame_canvas.offset_x
        canvas_width = self.flame_canvas.width()
        StatusView.draw_all(
            self.timeline_canvas,
            [
                view
                for view in self.sample_statuses()
                if not view.offscreen(canvas_scale_x, canvas_offset_x, canvas_width)
            ],
        )

    def draw_markers(self) -> None:
        """Draw the marker views on the timeline canvas."""
        canvas_scale_x = self.flame_canvas.scale_x
        canvas_offset_x = self.flame_canvas.offset_x
        canvas_width = self.flame_canvas.width()
        MarkerView.draw_all(
            self.timeline_canvas,
            [
                view
                for view in self.markers
                if not view.offscreen(canvas_scale_x, canvas_offset_x, canvas_width)
            ],
        )

    def draw(self) -> None:
        """Draw the flamegraph and timeline."""
        self.draw_timeline()
        self.draw_flame()

    def draw_flame(self, _event: Any | None = None) -> None:
        """Draw the flamegraph on the flame canvas."""
        self.clear(self.flame_canvas)
        canvas_scale_x = self.flame_canvas.scale_x
        canvas_offset_x = self.flame_canvas.offset_x
        canvas_width = self.flame_canvas.width()
        CallView.draw_all(
            self.flame_canvas,
            [
                view
                for view in self.calls
                if not view.offscreen(canvas_scale_x, canvas_offset_x, canvas_width)
            ],
        )

    def sample_statuses(self) -> list[Any]:
        """Sample statuses to reduce the number of views drawn on the timeline."""
        if not self.statuses:
            return []
        statuses = [self.statuses[0]]
        sample = int(max(1, 1 / self.flame_canvas.scale_x / 4))
        for n, status in enumerate(self.statuses):
            if n % sample == 0:
                statuses.append(status)
        statuses.append(self.statuses[-1])
        return statuses

    def flame_mousemove(self, event: Any) -> None:
        """Handle mouse movement over the flame canvas."""
        self.mousemove_canvas(self.flame_canvas, self.calls, event)

    def timeline_mousemove(self, event: Any) -> None:
        """Handle mouse movement over the timeline canvas."""
        self.mousemove_canvas(self.timeline_canvas, self.statuses, event)
        self.mousemove_canvas(self.timeline_canvas, self.markers, event)

    def mousemove_canvas(self, canvas: Any, views: list[Any], event: Any) -> None:
        """Handle mouse movement over a given canvas and its views."""
        if canvas.is_dragging() or not hasattr(event.originalEvent, "offsetX"):
            return
        x, y, _, _ = canvas.absolute(
            event.originalEvent.offsetX, event.originalEvent.offsetY
        )
        canvas_scale_x = self.flame_canvas.scale_x
        canvas_offset_x = self.flame_canvas.offset_x
        canvas_width = self.flame_canvas.width()
        for view in views:
            if not view.offscreen(
                canvas_scale_x, canvas_offset_x, canvas_width
            ) and view.inside(x, y):
                if self.hover is not view:
                    if self.hover:
                        self.hover.mouseleave(x, y)
                    view.mouseenter(x, y)
                    self.hover = view
                view.mousemove(x, y)

    def click_flame(self, x: float, y: float) -> None:
        """Handle click events on the flame canvas."""
        self.click_canvas(self.flame_canvas, self.calls, x, y)

    def click_timeline(self, x: float, y: float) -> None:
        """Handle click events on the timeline canvas."""
        self.click_canvas(self.timeline_canvas, self.markers, x, y)

    def click_canvas(self, canvas: Any, views: list[Any], x: float, y: float) -> bool:
        """Handle click events on a given canvas and its views."""
        x, y, _, _ = canvas.absolute(x, y)
        for view in views:
            if view.inside(x, y):
                view.click(x, y)
                return True
        dialog.hide()
        CallView.selected = None
        self.draw()
        return False

    def reset(self) -> None:
        """Reset the flamegraph and timeline to their initial states."""
        self.timeline_canvas.reset()
        self.flame_canvas.reset()
        self.hover = None
        CallView.reset()
        StatusView.reset()
        MarkerView.reset()

    def convert_log(self) -> None:
        """
        Convert the current recording into lists of CallView, StatusView, and
        MarkerView instances.
        """
        self.calls = [CallView(self.flame_canvas, model) for model in recording.calls]
        self.statuses = [
            StatusView(self.timeline_canvas, model) for model in recording.statuses
        ]
        self.markers = [
            MarkerView(self.timeline_canvas, model) for model in recording.markers
        ]

    def add_marker_to_log_tab(
        self, log_entries: list[tuple[float, str, str]], index: int
    ) -> None:
        """Add a marker entry to the log tab if available."""
        if self.statuses and index < len(self.statuses):
            log_entries.append(
                (self.statuses[index].when, str(self.statuses[index]), "")
            )

    def add_message_to_log_tab(
        self,
        log_entries: list[tuple[float, str, str]],
        when: float,
        message: str,
        stack: str = "",
    ) -> None:
        """Add a custom message entry to the log tab."""
        log_entries.append((when, message, stack))

    def load(self) -> None:
        """Load and process the current recording, updating the visualizations and log tab."""
        self.convert_log()
        status_index = 0
        log_entries: list[tuple[float, str, str]] = []
        self.add_marker_to_log_tab(log_entries, 0)
        for marker in self.markers:
            if self.statuses:
                while (
                    self.statuses[status_index].when < marker.when
                    and status_index < len(self.statuses) - 1
                ):
                    status_index += 1
            log_entries.append(
                (
                    marker.when,
                    markdown.to_html(marker.message),
                    marker.format_stack(),
                )
            )
            self.add_marker_to_log_tab(log_entries, status_index)
        for call in [call for call in self.calls if call.slow_import()]:
            self.add_message_to_log_tab(
                log_entries,
                call.when,
                f"😡 Slow import {call.call_site.name.replace('..<module>', '')} " \
                    f"took {call.duration}s",
            )
        self.add_log_entries(log_entries)
        self.add_marker_to_log_tab(log_entries, -1)
        self.hover = None
        js.jQuery(self.flame_element_id).empty()
        js.jQuery(self.timeline_element_id).empty()

    def add_log_entries(self, log_entries: list[tuple[float, str, str]]) -> None:
        """Add log entries to the log tab in batches to avoid blocking the UI."""
        js.jQuery("#tabs-log").empty()
        log_entries.sort(key=lambda entry: entry[0])
        batch_size = 10
        total_entries = len(log_entries)

        def process_batch(start_index: int) -> None:
            end_index = min(start_index + batch_size, total_entries)
            batch = log_entries[start_index:end_index]

            js.jQuery("#tabs-log").append(*map(lambda entry: self.get_log_entry(*entry), batch))
            if end_index < total_entries:
                js.setTimeout(ltk.proxy(lambda: process_batch(end_index)))
            else:
                js.jQuery(".log-stack").click(
                    ltk.proxy(lambda event: self.show_log_stack(event)) # pylint: disable=unnecessary-lambda
                )

        if log_entries:
            js.setTimeout(ltk.proxy(lambda: process_batch(0)), 1000)
        else:
            js.jQuery("#tabs-log").append("No log entries found")

    def get_log_entry(self, when: float, entry: str, stack: str) -> str:
        """Format a single log entry as HTML."""
        stack_index = len(self.stacks)
        self.stacks[stack_index] = stack or "Missing stack for this log entry"
        stack_entry = [
            ltk.Span("Stack")
                .addClass("log-stack")
                .attr("index", stack_index),
            ltk.Div()
                .addClass("log-stack-toggle")
                .attr("id", f"log-stack-{stack_index}"),
        ] if stack else []
        return (
            ltk.Div()
                .addClass("log-entry")
                .append(
                    ltk.Span(f"At&nbsp;{when:0.2f}s")
                        .addClass("log-when"),
                    *stack_entry,
                    ltk.Div(ltk.Preformatted(colorize(entry)))
                        .addClass("log-message")
                )
        )

    def show_log_stack(self, event: Any) -> None:
        """Display the stack trace for a log entry when clicked."""
        target = js.jQuery(event.target)
        index = int(target.attr("index") or "0")
        stack = self.stacks.get(index, "").replace("\n", "<br>")
        js.jQuery(f"#log-stack-{index}").html(f"<br>{stack}")

    def loading(self, name: str) -> None:
        """Display a loading message while processing a recording."""
        self.show_message(f"Analyzing recording {name}...")

    def show_message(self, message: str) -> None:
        """Display a message ."""
        self.clear()
        self.flame_canvas.text(60, 10, message, color="pink", font="16px Arial")
