#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Call view management for Microlog dashboard."""

from __future__ import annotations

import itertools
import re
from typing import Any

import ltk
import js
from microlog import api
from microlog.dashboard import colors
from microlog.dashboard import config
from microlog.dashboard.canvas import Canvas
from microlog.dashboard.dialog import dialog
from microlog.dashboard.views import View
from microlog.dashboard.views import sanitize
from microlog.dashboard.views import status
from microlog.models import Call


class CallView(View):
    """A visual representation of a function call in the call graph."""

    thread_index: dict[str, int] = {}
    show_threads: set[str] = set()
    instances: list["CallView"] = []
    min_width: int = 3
    selected: "CallView | None" = None
    canvas: Canvas | None = None

    def __init__(self, canvas: Canvas, model: Call) -> None:
        """Initialize a CallView instance."""
        self.model: Call = model
        View.__init__(self, canvas)
        CallView.canvas = canvas
        self.x = self.y = self.w = self.h = 0
        self.color = colors.get_color(self.model.call_site.name)
        self.index = len(CallView.instances)
        CallView.instances.append(self)

        if self.model.thread_id not in self.thread_index:
            self.thread_index[self.model.thread_id] = len(self.thread_index)
            if len(self.thread_index) <= 1:
                self.show_threads.add(self.model.thread_id)

            def redraw(_: Any) -> None:
                self.show_threads.clear()
                self.show_threads.add(self.model.thread_id)
                js.jQuery(".thread-selector").prop("checked", False)
                js.jQuery(f"#toggle-{self.model.thread_id}").prop("checked", True)
                canvas.redraw()

            js.jQuery(".flamegraph-container").append(
                (
                    js.jQuery("<input>")
                    .addClass("thread-selector")
                    .prop("type", "checkbox")
                    .prop("checked", "" if len(self.thread_index) > 1 else "checked")
                    .attr("id", f"toggle-{self.model.thread_id}")
                    .attr("threadId", self.model.thread_id)
                    .css(
                        "top",
                        canvas.offset_y + 227 + 60 * self.thread_index[self.model.thread_id],
                    )
                    .on("click", ltk.proxy(redraw))
                ),
                js.jQuery("#timelineCanvas"),
            )
        self.y = self.model.depth * config.LINE_HEIGHT + \
                60 * self.thread_index[self.model.thread_id]

    def calculate(self) -> None:
        """Calculate the call's position and size."""
        self.x = self.when * config.PIXELS_PER_SECOND
        self.y = self.model.depth * config.LINE_HEIGHT
        self.w = self.duration * config.PIXELS_PER_SECOND
        self.h = config.LINE_HEIGHT

    def is_import(self) -> bool:
        """Return True if this call is an import (<module>)."""
        name = self.model.call_site.name
        return name.endswith("<module>")

    def get_full_name(self) -> str:
        """Return the full name for this call, with emoji if slow import."""
        module_name, name = self.model.call_site.name.rsplit(".", 1)
        if name == "<module>":
            name = f"import {module_name}"
        else:
            name = self.model.call_site.name
        return f"😡 {name}" if self.slow_import() else name

    def get_short_name(self) -> str:
        """Return a short name for this call, with emoji if slow import."""
        parts = self.model.call_site.name.split(".")
        name = parts[-1]
        if name in ("__init__", "<module>"):
            name = parts[-2] or parts[-3]
        return f"😡 {name}" if self.slow_import() else name

    def slow_import(self) -> bool:
        """Return True if this is a slow import call."""
        return self.model.depth > 0 and self.model.duration > 0.1 and self.is_import()

    def get_label(self) -> str:
        """Return a label for this call based on width."""
        w = CallView.canvas.to_screen_dimension(self.w)
        if w > 300:
            return f"{self.get_full_name()} (at {self.model.when:0.2f} " \
                f"duration: {self.model.duration:0.2f}s)"
        elif w > 200:
            return f"{self.get_short_name()} (at {self.model.when:0.2f} " \
                f"duration: {self.model.duration:0.2f}s)"
        else:
            return self.get_short_name()

    @classmethod
    def reset(cls) -> None:
        """Reset all CallView instances and thread selectors."""
        CallView.instances.clear()
        CallView.selected = None
        cls.thread_index = {}
        js.jQuery(".thread-selector").remove()

    @classmethod
    def get_thread_index(cls, canvas: Any, thread_id: str) -> int:
        """Get or assign a thread index for a given thread ID."""
        if thread_id not in cls.thread_index:
            cls.thread_index[thread_id] = len(cls.thread_index)
            if len(cls.thread_index) <= 1:
                cls.show_threads.add(thread_id)

            def redraw(_: Any) -> None:
                if thread_id in cls.show_threads:
                    cls.show_threads.remove(thread_id)
                else:
                    cls.show_threads.add(thread_id)
                canvas.redraw()

            js.jQuery(".flamegraph-container").append(
                (
                    js.jQuery("<input>")
                    .addClass("thread-selector")
                    .prop("type", "checkbox")
                    .prop("checked", "" if len(cls.thread_index) > 1 else "checked")
                    .attr("id", f"toggle-{thread_id}")
                    .attr("threadId", thread_id)
                    .css("top", canvas.offset_y + 227 + 60 * cls.thread_index[thread_id])
                    .on("change", ltk.proxy(redraw))
                ),
                js.jQuery("#timelineCanvas"),
            )
        return cls.thread_index[thread_id]

    @classmethod
    def position_threads(cls, canvas: Any) -> None:
        """Position thread selector checkboxes in the UI."""
        threads = js.jQuery(".thread-selector")
        for index in range(threads.length):
            thread = threads.eq(index)
            thread.css("top", canvas.offset_y + 227 + 60 * index)

    def matches(self, query: Any) -> bool:
        """Return True if this call matches the search query."""
        if not query:
            return True
        return re.search(query, self.get_full_name().lower()) is not None

    @classmethod
    def draw_all(cls, canvas: Canvas, calls: list["CallView"]) -> None:
        """Draw all CallView instances on the canvas."""
        query = re.compile(js.jQuery(".span-search").val().lower())
        canvas.clear("#222")
        canvas.fill_rects(
            (
                call.x,
                call.y,
                call.w,
                call.h,
                call.color if call.matches(query) else "#333",
            )
            for call in calls
            if canvas.to_screen_dimension(call.w) > cls.min_width
            and call.thread_id in cls.show_threads
        )
        dx = canvas.from_screen_dimension(4)
        canvas.texts(
            [
                (
                    call.x + dx,
                    call.y + call.h - 8,
                    call.get_label(),
                    "#111" if call.matches(query) else "#999",
                    call.w - 2 * dx,
                )
                for call in calls
                if canvas.to_screen_dimension(call.w) > cls.min_width
                and call.thread_id in cls.show_threads
            ],
            config.FONT_REGULAR,
        )
        if js.jQuery(".thread-selector").length < 2:
            js.jQuery(".thread-selector").css("display", "none")
        canvas.lines(
            itertools.chain(
                [
                    (call.x, call.y, call.x, call.y + call.h)
                    for call in calls
                    if canvas.to_screen_dimension(call.w) > cls.min_width
                    and call.thread_id in cls.show_threads
                ]
            ),
            1,
            "gray",
        )
        canvas.lines(
            itertools.chain(
                [
                    (call.x, call.y + call.h, call.x + call.w, call.y + call.h)
                    for call in calls
                    if canvas.to_screen_dimension(call.w) > cls.min_width
                    and call.thread_id in cls.show_threads
                ]
            ),
            1,
            "gray",
        )
        if cls.selected:
            cls.selected.draw("red", "white")
        js.jQuery(".py-error").on(
            "click",
            ltk.proxy(lambda event: js.jQuery(event.target).remove()),
        )

    def inside(self, x: float, y: float) -> bool:
        """Return True if the given coordinates are inside this call's area."""
        return (
            self.model.thread_id in self.show_threads
            and CallView.canvas.to_screen_dimension(self.w) > self.min_width
            and View.inside(self, x, y)
        )

    def draw(self, fill: str, color: str) -> None:
        """Draw this call on the canvas."""
        if self.model.thread_id not in self.show_threads:
            return
        w = CallView.canvas.to_screen_dimension(self.w)
        if w > 0:
            CallView.canvas.fill_rect(self.x, self.y, self.w, self.h - 1, fill)
            CallView.canvas.line(self.x, self.y, self.x + self.w, self.y, 1, "#DDD")
            CallView.canvas.line(self.x, self.y, self.x, self.y + self.h, 1, "#AAA")
        if w > self.min_width:
            dx = CallView.canvas.from_screen_dimension(4)
            CallView.canvas.text(
                self.x + dx, self.y + 2, self.get_label(), color, self.w - 2 * dx
            )

    def click(self, x: float, y: float) -> None:
        """Handle click event on this call."""
        if not CallView.canvas.is_dragging():
            x = CallView.canvas.canvas.position().left + CallView.canvas.to_screen_x(self.x) + 50
            y = CallView.canvas.canvas.position().top + CallView.canvas.to_screen_y(self.y) + 50
            self.show_popup(x, y)

    def module_count(self) -> int:
        """Return the number of modules loaded during this call."""
        begin = status.StatusView.get_status_at(self.model.when)
        end = status.StatusView.get_status_at(self.model.when + self.model.duration)
        if begin and end:
            return end.model.module_count - begin.model.module_count
        return 0

    def show_popup(self, x: float, y: float) -> None:
        """Show a popup dialog with details about this call."""
        if CallView.canvas.is_dragging():
            return
        if dialog.showing and CallView.selected is self:
            dialog.hide()
            CallView.selected = None
            return
        CallView.selected = self
        CallView.canvas.redraw()
        similar = [call for call in CallView.instances if self.is_similar(call)]
        total = sum(call.duration for call in similar)
        percentage = min(100, total / status.StatusView.last_when * 100)
        print(percentage, len(CallView.instances), len(similar))
        average = total / len(similar) if similar else 0
        anomalies = [
            call
            for call in similar
            if call.duration - average > 0.1 and call.duration / average > 1.3
        ]
        cpu = self.get_cpu()
        details_id = f"call-details-{id(self)}"
        name = sanitize(self.model.call_site.name).replace("..", ".")
        link = api.create_link(self.model.call_site.filename, self.model.call_site.lineno, name)
        kind = "import" if self.is_import() else "call"
        dialog.show(
            CallView.canvas,
            x,
            y,
            "".join([
                f"""<b>{link}</b> <br>""",
                """<span style="color:red">😡 Slow import detected!</span><br>"""
                if self.slow_import() else "",
                f"""This {kind} at {self.model.when:.3f}s took {self.model.duration:.3f}s.<br>""",
            ] + ([
                f"""Total duration: {total:.3f}s for {len(similar)} {kind}s.<br>""",
                f"""Average duration: {average:.3f}s.<br>"""
            ] if len(similar) > 1 else [
            ]) + [
                f"""Time spent inside this {kind} is {percentage:.2f}% of total.<br>""",
                f"""During this {kind}, {self.module_count()} modules were loaded.<br>""",
                f"""CPU usage during this {kind}: {cpu:.1f}% {"😡" if cpu < 80 else ""}.<br>""",
                f"""<div id="{details_id}"><br><span style="color:gray">""",
                """loading details...</span></div>""",
            ]),
        )
        if len(similar) > 1000:
            js.setTimeout(
                ltk.proxy(
                    lambda: self.add_similar_calls(
                        f"#{details_id}", cpu, similar, anomalies
                    )
                ),
                1,
            )
        else:
            self.add_similar_calls(f"#{details_id}", cpu, similar, anomalies)

        js.jQuery(".call-index").click(
            ltk.proxy(
                lambda event: self.highlight_call(js.jQuery(event.target))
            )
        )
        self.draw("red", "white")

    def highlight_call(self, link: Any) -> None:
        """Highlight the call corresponding to the clicked link."""
        CallView.selected = CallView.instances[int(link.attr("index"))]
        CallView.canvas.redraw()

    def mouseenter(self, x: float, y: float) -> None:
        """Handle mouse enter event for highlighting."""
        View.mouseenter(self, x, y)
        left = CallView.canvas.to_screen_x(self.x)
        top = (
            CallView.canvas.to_screen_y(self.y)
            + config.FLAME_OFFSET_Y
            + config.TIMELINE_HEIGHT
            + 4
        )
        w = CallView.canvas.to_screen_dimension(self.w)
        h = config.LINE_HEIGHT
        if (
            self.model.thread_id in self.show_threads
            and CallView.canvas.to_screen_dimension(self.w) > self.min_width
        ):
            js.jQuery(".call-highlight").appendTo(CallView.canvas.canvas.parent())
            js.jQuery("#call-highlight-top").css("left", left).css("top", top).css(
                "width", w
            ).css("height", 0)
            js.jQuery("#call-highlight-bottom").css("left", left).css(
                "top", top + h
            ).css("width", w).css("height", 0)
            js.jQuery("#call-highlight-left").css("left", left).css("top", top).css(
                "width", 0
            ).css("height", h)
            js.jQuery("#call-highlight-right").css("left", left + w).css(
                "top", top
            ).css("width", 0).css("height", h)

    def mouseleave(self, x: float, y: float) -> None:
        """Handle mouse leave event for removing highlight."""
        View.mouseleave(self, x, y)

    def get_cpu(self) -> float:
        """Return average CPU usage during this call."""
        stats = [
            view
            for view in status.StatusView.instances
            if view.when >= self.model.when and view.when <= self.model.when + self.model.duration
        ]
        return sum(stat.cpu for stat in stats) / len(stats) if stats else 0

    def is_anomaly(self, call: "CallView", anomalies: list["CallView"]) -> bool:
        """Return True if the call is in the anomalies list."""
        for anomaly in anomalies:
            if call is anomaly:
                return True
        return False

    def get_all_calls(self, similar: list["CallView"], anomalies: list["CallView"]) -> str:
        """Return HTML for all similar calls and their durations."""
        max_duration = max(call.duration for call in similar)

        def color(call: "CallView") -> str:
            return "red" if self.is_anomaly(call, anomalies) else "green"

        return "".join(
            [
                f"""<tr>
                <td class="td-number"><a class="call-index" index={call.index} href=#>
                    {call.when:.3f}s</a>
                </td>
                <td class="td-number">{call.duration:.3f}s</td>
                <td><div style=
                    "background: {color(call)};
                     height: 12px;width:{call.duration * 150 / max_duration}px
                    "></div></td>
            </tr>"""
                for call in sorted(similar, key=lambda call: -call.duration)
            ]
        )

    def get_similar_call_html(
        self, similar: list["CallView"], anomalies: list["CallView"]
    ) -> str:
        """Return HTML for the list of similar calls."""
        return f"""<br>This function is called {len(similar)} times:
            <div style="
                height: 300px;
                overflow-y: auto;
            ">
                <table>
                    <hr>
                        <td style="text-align: right"><b>When</b></td>
                        <td style="text-align: right"><b>&nbsp;&nbsp;Time</b></td>
                </hr>
                {self.get_all_calls(similar, anomalies)}
                </table>
            </div>
        """

    def get_anomalies_html(self, _cpu: float, anomalies: list["CallView"]) -> str:
        """Return HTML for the list of anomalies."""
        anomaly = "is an anomaly" if self.is_anomaly(self, anomalies) else "looks average"
        return f"""
            <br>
            <img src="data:image/webp;base64,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">
            <br>
            Microlog detected {len(anomalies)} anomalies.<br>
            The current call {anomaly}.<br>
        """

    def add_similar_calls(
        self,
        details_id: str,
        cpu: float,
        similar: list["CallView"],
        anomalies: list["CallView"],
    ) -> None:
        """Add HTML for similar calls and anomalies to the dialog."""
        parts = []
        if len(anomalies) > 1:
            parts.append(self.get_anomalies_html(cpu, anomalies))
        if len(similar) > 1:
            parts.append(self.get_similar_call_html(similar, anomalies))
        js.jQuery(details_id).html("".join(parts))

    def is_similar(self, other: "CallView") -> bool:
        """Check if another CallView is similar to this one."""
        return (
            self.model.call_site == other.call_site
            and self.model.caller_site == other.caller_site
        )

    def __eq__(self, other: object) -> bool:
        """Check equality with another CallView based on call site and caller site."""
        return (
            isinstance(other, CallView)
            and self.model.call_site == other.call_site
            and self.model.caller_site == other.caller_site
        )
