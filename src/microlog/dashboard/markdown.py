#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Markdown to HTML convertor"""

from textwrap import dedent


def to_html(markdown_text: str) -> str:
    """Convert markdown to html"""
    prev_indent: int = -1
    html: list[str] = []
    fenced: bool = False
    for _, line in enumerate(
        dedent(markdown_text).replace("\\n", "\n").strip().split("\n"), 1
    ):
        if line.strip() in ["---", "```"]:
            if fenced:
                html.append("</pre>")
                fenced = False
            else:
                fenced = True
                html.append("<pre>")
            continue

        if fenced:
            for _ in range(prev_indent):
                if line and line[0] == " ":
                    line = line[1:]
            html.append(line)
            html.append("<br>")
            continue

        indent = prev_indent
        if line:
            indent = 0
            while line and line[0] == " ":
                indent += 1
                line = line[1:]
        if indent > prev_indent and prev_indent != -1:
            html.append("<ul style='margin-block-start: 0; margin-bottom: 20px'>")
        if indent < prev_indent:
            html.append("</ul>")

        if line == "":
            html.append("<br>")
        elif len(line) > 3 and line[0:3] == "###":
            html.append(f"<h3>{line[3:].strip()}</h3>")
        elif len(line) > 2 and line[0:2] == "##":
            html.append(f"<h2>{line[2:].strip()}</h2>")
        elif line[0] == "#":
            html.append(f"<h1>{line[1:].strip()}</h1>")
        elif line[0] == "-":
            html.append(f"<li>{line[1:]}</li>")
        else:
            html.append(f"{line}<br>")
        prev_indent = indent
    html.append("</h1>")
    html.append("</h2>")
    html.append("</h3>")
    html.append("</ul>")
    return "".join(html)
