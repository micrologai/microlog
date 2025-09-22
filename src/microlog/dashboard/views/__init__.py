#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Base view class for Microlog dashboard visual elements."""

from __future__ import annotations

from typing import Any

from microlog.dashboard import config
from microlog.dashboard.canvas import Canvas


def sanitize(text: str) -> str:
    """Sanitize text for HTML display."""
    return text.replace("<", "&lt;").replace("\\n", "<br>")


class View:
    """Base class for dashboard visual elements."""

    def __init__(self, canvas: Canvas) -> None:
        """Initialize a View with position and size."""
        self.canvas: Canvas = canvas
        self.x: float = self.when * config.PIXELS_PER_SECOND
        self.y: float = 0
        self.w: float = self.duration * config.PIXELS_PER_SECOND
        self.h: float = 0

    def __eq__(self, other: object) -> bool:
        """Check equality with another View instance."""
        return self is not other

    def mouseenter(self, _x: float, _y: float) -> None:
        """Handle mouse enter event."""

    def mousemove(self, x: float, y: float) -> None:
        """Handle mouse move event."""

    def click(self, x: float, y: float) -> None:
        """Handle click event."""

    def mouseleave(self, _x: float, _y: float) -> None:
        """Handle mouse leave event."""
        self.canvas.css("cursor", "default")

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying model."""
        return getattr(self.model, name)

    def inside(self, x: float, y: float) -> bool:
        """Check if coordinates are inside the view area."""
        return (
            x >= self.x and x < self.x + self.w and y >= self.y and y < self.y + self.h
        )

    def calculate(self) -> None:
        """Calculate view properties (override in subclasses if needed)."""

    def offscreen(self, scale_x: float, offset_x: float, width: float) -> bool:
        """Check if the view is offscreen given scale and offset."""
        self.calculate()
        x = self.x * scale_x + offset_x
        w = self.w * scale_x
        return w < 2 or x + w < 0 or x > width
