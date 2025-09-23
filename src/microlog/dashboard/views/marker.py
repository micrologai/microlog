#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Marker view for Microlog dashboard."""

from __future__ import annotations

from typing import Any

import logging
import ltk
import js
import microlog.api as api
import microlog.config as main_config
from microlog.dashboard import config
from microlog.dashboard import markdown
from microlog.dashboard.dialog import dialog
from microlog.dashboard.views import View
from microlog.models import CALLSITE_UNKNOWN
from microlog.models import CallSite
from microlog.models import Marker


class MarkerView(View):
    """A visual representation of a log marker in the dashboard."""

    radius: int = 10
    colors: dict[int, str] = {
        logging.INFO: "#FFFF00",
        logging.WARN: "#F97B41",
        logging.DEBUG: "#FF00FF",
        logging.ERROR: "#FF0000",
        main_config.EVENT_KIND_INFO: "#FFFF00",
        main_config.EVENT_KIND_ERROR: "#FF0000",
    }
    border_colors: dict[int, str] = {
        logging.INFO: "#5F5F5B",
        logging.WARN: "#989290",
        logging.DEBUG: "#FAABFA",
        logging.ERROR: "#FFABAB",
        main_config.EVENT_KIND_INFO: "#5F5F5B",
        main_config.EVENT_KIND_ERROR: "#FFABAB",
    }
    offset: dict[int, int] = {
        logging.INFO: 0,
        logging.WARN: 12,
        logging.DEBUG: 24,
        logging.ERROR: 36,
        main_config.EVENT_KIND_INFO: 0,
        main_config.EVENT_KIND_ERROR: 36
    }
    names: dict[int, str] = {
        logging.INFO: "INFO",
        logging.WARN: "WARN",
        logging.DEBUG: "DEBUG",
        logging.ERROR: "ERROR",
        main_config.EVENT_KIND_INFO: "INFO",
        main_config.EVENT_KIND_ERROR: "ERROR",
    }
    instances: list["MarkerView"] = []

    def __init__(self, canvas: Any, model: Marker) -> None:
        """Initialize a MarkerView instance."""
        self.model: Marker = model
        View.__init__(self, canvas)
        self.color: str = (
            self.colors[self.kind]
            if self.kind in self.colors
            else "white"
        )
        self.border_color: str = (
            self.border_colors[self.kind]
            if self.kind in self.border_colors
            else "white"
        )
        self.x = self.when * config.PIXELS_PER_SECOND - self.canvas.from_screen_dimension(
            self.radius / 2
        )
        self.w = self.canvas.from_screen_dimension(self.radius)
        self.h = self.canvas.from_screen_dimension(self.radius)
        self.index: int = len(MarkerView.instances)
        self.call_site: CallSite = CALLSITE_UNKNOWN
        MarkerView.instances.append(self)

    @classmethod
    def reset(cls) -> None:
        """Reset all MarkerView instances."""
        MarkerView.instances.clear()

    @classmethod
    def draw_all(cls, _canvas: Any, markers: list["MarkerView"]) -> None:
        """Draw all MarkerView instances on the canvas."""
        query = js.jQuery(".span-search").val().lower()
        for marker in markers:
            marker.draw(query)

    def get_full_name(self) -> str:
        """Return the full name for this marker's call site."""
        return self.call_site.name

    def get_short_name(self, name: str | None = None) -> str:
        """Return a short name for this marker's call site."""
        if name is None:
            name = self.call_site.name
        parts = name.split(".")
        name = parts[-1]
        if name in ("__init__", "<module>"):
            name = parts[-2] or parts[-3]
        return name

    def calculate(self) -> None:
        """Calculate the marker's position and size."""
        self.x = (
            self.when * config.PIXELS_PER_SECOND
            - self.canvas.from_screen_dimension(self.radius / 2)
        )
        self.y = 115 - self.offset.get(self.kind, 0)
        self.w = self.canvas.from_screen_dimension(self.radius)

    def matches(self, query: Any) -> bool:
        """Return True if the marker matches the search query."""
        if not query:
            return True
        query = query.lower()
        return (
            query in self.message.lower()
            or query in self.get_short_name().lower()
            or any(query in call_site.name.lower() for call_site in self.stack)
        )

    def draw(self, query: str | None = None) -> None:
        """Draw this marker on the canvas."""
        color = self.color if self.matches(query) else "#555"
        border = (
            self.border_color
            if not query or query in self.message.lower()
            else "#333"
        )
        self.canvas.circle(
            self.x + self.w / 2,
            self.y + self.radius / 2,
            self.w / 2,
            color,
            1,
            border,
        )

    def mouseenter(self, x: float, y: float) -> None:
        """Handle mouse enter event for highlighting."""
        View.mouseenter(self, x, y)
        self.select()

    def select(self) -> None:
        """Highlight this marker and show its details."""
        query = js.jQuery(".span-search").val().lower()
        self.draw(query)
        (
            js.jQuery("#marker-highlight")
            .attr("index", self.index)
            .css("left", self.canvas.to_screen_x(self.x) - 1)
            .css("top", self.canvas.to_screen_y(self.y) + 35)
            .css("width", self.canvas.to_screen_dimension(self.w) - 1)
            .css("height", self.radius - 2)
            .appendTo(self.canvas.canvas.parent())
        )

    def mouseleave(self, x: float, y: float) -> None:
        """Handle mouse leave event for removing highlight."""
        View.mouseleave(self, x, y)

    def format_stack(self) -> str:
        """Format the stack trace for display."""
        return "<br>".join(
            [
                f"{api.create_link(call_site.filename, call_site.lineno)} in " \
                    f"{self.get_short_name(call_site.name)}"
                for call_site in self.stack
            ]
        )

    def click(self, x: float, y: float) -> None:
        """Handle click event to show marker details dialog."""
        self.select()
        formatted_stack = self.format_stack()
        stack = (
            f"""
            <h2>Callstack</h2>
            <pre>{formatted_stack}</pre>
        """
            if formatted_stack
            else ""
        )

        message = markdown.to_html(self.message.strip())
        html = f"""
            <button id='prev-marker'>&lt;</button>
            Log entry {self.index + 1:,} of {len(MarkerView.instances):,}
            <button id='next-marker'>&gt;</button>
            &nbsp; &nbsp; &nbsp; &nbsp;
            {self.names.get(self.kind, f"Unknown: {self.kind}")}
            @ {self.when:.3f}s
            &nbsp; &nbsp; &nbsp; &nbsp;
            <button id='show-log'>show full log</button>
            <br><br>
            <pre>{message}</pre>
            {stack}
        """
        x = self.canvas.canvas.position().left + self.canvas.to_screen_x(self.x) + 50
        y = self.canvas.canvas.position().top + self.canvas.to_screen_y(self.y) + 50
        dialog.show(self.canvas, x, y, html, 14)
        js.jQuery("#prev-marker").click(
            ltk.proxy(
                lambda event: MarkerView.instances[max(0, self.index - 1)].click(x, y)
            )
        )
        js.jQuery("#next-marker").click(
            ltk.proxy(
                lambda event: MarkerView.instances[
                    min(len(MarkerView.instances) - 1, self.index + 1)
                ].click(x, y)
            )
        )
        js.jQuery("#show-log").click(
            ltk.proxy(lambda event: self.show_log())
        )

    def show_log(self) -> None:
        """Show the full log tab for this marker."""
        dialog.hide()
        js.jQuery('a[href="#ltk-tabs-0-1"]').click()


def click_marker(event: Any) -> None:
    """Handle click event for marker highlight."""
    index = int(js.jQuery("#marker-highlight").attr("index"))
    x = event.originalEvent.offsetX
    y = event.originalEvent.offsetY
    MarkerView.instances[index].click(x, y)


js.jQuery("#marker-highlight").click(ltk.proxy(click_marker))
