#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Dialog box management for Microlog dashboard."""

from __future__ import annotations

from typing import Any

import ltk

import js
from microlog.dashboard.canvas import Canvas
from microlog.dashboard.colors import colorize


FLIP_DISTANCE: int = 70
MOUSE_OFFSET: int = 20


class Dialog:
    """A draggable and resizable dialog box for displaying information."""

    def __init__(self) -> None:
        self.showing: bool = False
        self.dialog: Any = ltk.find("#dialog")
        self.canvas: Canvas | None = None

    def show(self, canvas: Canvas, x: float, y: float, html: str, font_size: int = 18) -> None:
        """Show the dialog box at the specified position with the given HTML content."""
        self.canvas = canvas
        self.dialog = ltk.find("#dialog")
        self.showing = True
        self.add_close_button()
        x = float(js.localStorage.getItem("dialog.x") or 0) or x
        y = float(js.localStorage.getItem("dialog.y") or 0) or y
        body = ltk.find("body").append(
            self.dialog
                .draggable()
                .resizable()
                .html(colorize(html))
                .addClass("dialog")
                .addClass("ui-widget-content")
                .css("position", "absolute")
                .css("display", "block")
                .css("font-size", font_size)
                .css("max-height", ltk.find("body").height() - 100)
                .on("dragstop", ltk.proxy(lambda *args: self.drag()))
        )
        x = min(max(x, 0), body.width() - self.dialog.width() - 50)
        y = min(max(y, 0), body.height() - self.dialog.height() -  50)
        self.dialog.css("left", x).css("top", y)

    def drag(self) -> None:
        """Handle the drag event to update the dialog's position in local storage."""
        js.localStorage.setItem(
            "dialog.x", max(50, js.parseFloat(self.dialog.css("left")))
        )
        js.localStorage.setItem(
            "dialog.y", max(50, js.parseFloat(self.dialog.css("top")))
        )

    def hide(self) -> None:
        """Hide the dialog box."""
        self.showing = False
        self.dialog.css("display", "none")

    def add_close_button(self) -> None:
        """Add a close button to the dialog box if not already present."""
        self.dialog.append(
            ltk.create("<div>")
                .addClass("dialog-close-button")
                .text("X")
                .click(ltk.proxy(lambda event: self.hide()))
        )


dialog: Dialog = Dialog()
