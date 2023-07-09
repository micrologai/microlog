#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

def toHTML(markdownText):
    import textwrap
    prevIndent = -1
    html = []
    fenced = False
    for lineno, line in enumerate(textwrap.dedent(markdownText).replace("\\n", "\n").strip().split("\n"), 1):
        # line = line.replace("<", "&lt;")
        if line.strip() in ["---", "```"]:
            if fenced:
                html.append("</pre>")
                fenced = False
            else:
                fenced = True
                html.append("<pre>")
            continue

        if fenced:
            for n in range(prevIndent):
                if line and line[0] == " ":
                    line = line[1:]
            html.append(line)
            html.append("<br>")
            continue

        indent = prevIndent
        if line:
            indent = 0
            while line and line[0] == " ":
                indent += 1
                line = line[1:]
        if indent > prevIndent and prevIndent != -1:
            html.append("<ul style='margin-block-start: 0; margin-bottom: 20px'>")
        if indent < prevIndent:
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
        prevIndent = indent
    html.append("</h1>")
    html.append("</h2>")
    html.append("</h3>")
    html.append("</ul>")
    return "".join(html)