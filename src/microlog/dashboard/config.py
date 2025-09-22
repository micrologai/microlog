#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Configuration constants for the Microlog dashboard application."""

from __future__ import annotations

import ltk


LINE_HEIGHT: int = 22
PIXELS_PER_SECOND: int = 100

FONT_SIZE_SMALL: int = 12
FONT_SIZE_REGULAR: int = 15
FONT_SIZE_LARGE: int = 20
FONT_NAME: str = "Arial"
FONT_SMALL: str = f"{FONT_SIZE_SMALL}px {FONT_NAME}"
FONT_REGULAR: str = f"{FONT_SIZE_REGULAR}px {FONT_NAME}"
FONT_LARGE: str = f"{FONT_SIZE_LARGE}px {FONT_NAME}"

STATS_OFFSET_Y: int = 0
STATS_HEIGHT: int = 140
TIMELINE_OFFSET_Y: int = STATS_OFFSET_Y + STATS_HEIGHT
TIMELINE_HEIGHT: int = 40
FLAME_OFFSET_Y: int = TIMELINE_OFFSET_Y + TIMELINE_HEIGHT + 2

BACKGROUND_COLOR: str = "#646363"

CALL_HOVER_DIALOG_DELAY: int = 500
MAX_STATUS_COUNT_FOR_MOVE: int = 1000

SCALE_MAX: int = 4096
SCALE_MIN: float = 0.032

CANVAS_INITIAL_OFFSET_X: int = 48
CANVAS_INITIAL_OFFSET_Y: int = 0
CANVAS_INITIAL_SCALE: float = 1.0

ZOOM_IN_FACTOR: float = 2.0
ZOOM_OUT_FACTOR: float = 0.5
MIN_ZOOM_FACTOR: float = 0.001
MIN_ZOOM_X: int = 48
MIN_ZOOM_Y: int = 48
MAX_ZOOM_X: int = -1000000
MAX_ZOOM_Y: int = -1000000

def tabs_height():
    """Calculate the height of the tabs navigation bar."""
    return ltk.find(".ui-tabs-nav").outerHeight()
