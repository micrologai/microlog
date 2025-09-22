#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Color management for Microlog dashboard."""

from __future__ import annotations


colors: dict[str, str] = {}

PASTEL: list[str] = [
    "#6ea1e2",
    "#efc1f2",
    "#acebff",
    "#ffb666",
    "#fffa99",
    "#e6e6e7",
    "#e6e6e7",
    "#bad8f7",
    "#f7e5ba",
]


def index(name: str, palette: list[str] = None) -> int:
    """Get a consistent index for a given name within the provided color palette."""
    try:
        palette = palette or PASTEL
        ordinals = ord(name[0]) + ord(name[round(len(name) / 2)]) + ord(name[-1])
        return ordinals % len(palette)
    except Exception: # pylint: disable=broad-except
        return 0


def get_color(name: str, palette: list[str] = None) -> str:
    """Get or assign a color for a given name from the specified palette."""
    palette = palette or PASTEL
    if name not in colors:
        colors[name] = palette[index(name)]
    return colors[name]


def colorize(html: str) -> str:
    """
    Colorize output to support ANSI colors in HTML format.
    """
    return (
        html
        # Reset codes
        .replace("\033[0m", "</span>")
        .replace("\033[00m", "</span>")
        # Foreground colors (normal intensity)
        .replace("\033[0;30m", "<span style='color:black;'>")
        .replace("\033[0;31m", "<span style='color:red;'>")
        .replace("\033[0;32m", "<span style='color:green;'>")
        .replace("\033[0;33m", "<span style='color:yellow;'>")
        .replace("\033[0;34m", "<span style='color:#3a8be6;'>")
        .replace("\033[0;35m", "<span style='color:magenta;'>")
        .replace("\033[0;36m", "<span style='color:cyan;'>")
        .replace("\033[0;37m", "<span style='color:white;'>")
        # Foreground colors (bold/bright)
        .replace("\033[1;30m", "<span style='color:gray; font-weight:bold'>")
        .replace("\033[1;31m", "<span style='color:red; font-weight:bold'>")
        .replace("\033[1;32m", "<span style='color:lime; font-weight:bold'>")
        .replace("\033[1;33m", "<span style='color:yellow; font-weight:bold'>")
        .replace("\033[1;34m", "<span style='color:#3a8be6; font-weight:bold'>")
        .replace("\033[1;35m", "<span style='color:magenta; font-weight:bold'>")
        .replace("\033[1;36m", "<span style='color:cyan; font-weight:bold'>")
        .replace("\033[1;37m", "<span style='color:white; font-weight:bold'>")
        # Underlined colors
        .replace("\033[4;30m", "<span style='color:black; text-decoration:underline'>")
        .replace("\033[4;31m", "<span style='color:red; text-decoration:underline'>")
        .replace("\033[4;32m", "<span style='color:green; text-decoration:underline'>")
        .replace("\033[4;33m", "<span style='color:yellow; text-decoration:underline'>")
        .replace(
            "\033[4;34m", "<span style='color:#3a8be6; text-decoration:underline'>"
        )
        .replace(
            "\033[4;35m", "<span style='color:magenta; text-decoration:underline'>"
        )
        .replace("\033[4;36m", "<span style='color:cyan; text-decoration:underline'>")
        .replace("\033[4;37m", "<span style='color:white; text-decoration:underline'>")
        # Background colors
        .replace("\033[40m", "<span style='background-color:black;'>")
        .replace("\033[41m", "<span style='background-color:red;'>")
        .replace("\033[42m", "<span style='background-color:green;'>")
        .replace("\033[43m", "<span style='background-color:yellow;'>")
        .replace("\033[44m", "<span style='background-color:#3a8be6;'>")
        .replace("\033[45m", "<span style='background-color:magenta;'>")
        .replace("\033[46m", "<span style='background-color:cyan;'>")
        .replace("\033[47m", "<span style='background-color:white;'>")
        # High intensity foreground colors
        .replace("\033[90m", "<span style='color:gray;'>")
        .replace("\033[91m", "<span style='color:lightcoral;'>")
        .replace("\033[92m", "<span style='color:lightgreen;'>")
        .replace("\033[93m", "<span style='color:lightyellow;'>")
        .replace("\033[94m", "<span style='color:lightblue;'>")
        .replace("\033[95m", "<span style='color:lightpink;'>")
        .replace("\033[96m", "<span style='color:lightcyan;'>")
        .replace("\033[97m", "<span style='color:white;'>")
        # High intensity background colors
        .replace("\033[100m", "<span style='background-color:gray;'>")
        .replace("\033[101m", "<span style='background-color:lightcoral;'>")
        .replace("\033[102m", "<span style='background-color:lightgreen;'>")
        .replace("\033[103m", "<span style='background-color:lightyellow;'>")
        .replace("\033[104m", "<span style='background-color:lightblue;'>")
        .replace("\033[105m", "<span style='background-color:lightpink;'>")
        .replace("\033[106m", "<span style='background-color:lightcyan;'>")
        .replace("\033[107m", "<span style='background-color:white;'>")
        # Simple foreground colors (without intensity prefix)
        .replace("\033[30m", "<span style='color:black;'>")
        .replace("\033[31m", "<span style='color:red;'>")
        .replace("\033[32m", "<span style='color:green;'>")
        .replace("\033[33m", "<span style='color:yellow;'>")
        .replace("\033[34m", "<span style='color:#3a8be6;'>")
        .replace("\033[35m", "<span style='color:magenta;'>")
        .replace("\033[36m", "<span style='color:cyan;'>")
        .replace("\033[37m", "<span style='color:white;'>")
        # Compound foreground colors
        .replace("\033[38;5;214m", "<span style='color:orange;'>")
    )
