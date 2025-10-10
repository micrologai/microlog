#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Markdown to HTML convertor"""

import re

styles = """
<style>
body {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
h1 {
    color: #4fc3f7;
    font-size: 2.5em;
    font-weight: 700;
    margin: 1.2em 0 0.8em 0;
    border-bottom: 3px solid #29b6f6;
    padding-bottom: 0.3em;
}
h2 {
    color: #81c784;
    font-size: 2em;
    font-weight: 600;
    margin: 1em 0 0.6em 0;
    border-bottom: 2px solid #66bb6a;
    padding-bottom: 0.2em;
}
h3 {
    color: #ffb74d;
    font-size: 1.5em;
    font-weight: 600;
    margin: 0.8em 0 0.4em 0;
    border-left: 4px solid #ff9800;
    padding-left: 0.5em;
}
h4 {
    color: #ba68c8;
    font-size: 1.2em;
    font-weight: 600;
    margin: 0.6em 0 0.3em 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
pre {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-left: 4px solid #0078d4;
    padding: 1rem;
    border-radius: 6px;
    margin: 1em 0;
    overflow-x: auto;
    font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
    font-size: 0.9em;
    line-height: 1.4;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    color: #f8f8f2;
}
code {
    background-color: #3c3c3c;
    color: #f92672;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
    font-size: 0.9em;
    border: 1px solid #555555;
}
strong { font-weight: 700; color: #ffffff; }
em { font-style: italic; color: #b0b0b0; }
a { color: #4fc3f7; text-decoration: none; transition: color 0.2s ease; }
a:hover { color: #29b6f6; text-decoration: underline; }
p { line-height: 1.7; margin: 0.8em 0; color: #e0e0e0; }
</style>
"""

def markdown(markdown_text: str) -> str:
    """Convert basic markdown to HTML"""
    html = markdown_text
    
    # Handle code blocks first (before other conversions)
    html = re.sub(r'```(\w+)?(.*?)\n```', r'\n<pre><code class="\1">\2</code></pre>\n', html, flags=re.DOTALL)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Headers
    html = re.sub(r'^#### (.*$)', r'#<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Paragraphs
    html = re.sub(r'\n\n', '</p><p>', html)
    html = f'<p>{html}</p>'
    html = html.replace('<p><h', '<h').replace('</h1></p>', '</h1>').replace('</h2></p>', '</h2>').replace('</h3></p>', '</h3>')
    html = html.replace('<p><pre>', '<pre>').replace('</pre></p>', '</pre>')
    
    return f"<html>{styles}{html}</html>"