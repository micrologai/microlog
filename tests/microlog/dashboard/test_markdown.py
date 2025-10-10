"""Tests for microlog.dashboard.markdown."""

import pytest

import microlog.dashboard.markdown as markdown_module


class TestMarkdownToHTML:
    """Test the markdown to HTML conversion functionality."""

    def test_simple_text(self):
        """Test that plain text is wrapped in paragraph tags."""
        result = markdown_module.markdown("Hello world")
        assert "<p>Hello world</p>" in result

    def test_headers(self):
        """Test header conversion."""
        # H1
        result = markdown_module.markdown("# Main Title")
        assert "<h1>Main Title</h1>" in result

        # H2
        result = markdown_module.markdown("## Section Title")
        assert "<h2>Section Title</h2>" in result

        # H3
        result = markdown_module.markdown("### Subsection Title")
        assert "<h3>Subsection Title</h3>" in result

    def test_bold_text(self):
        """Test bold text conversion."""
        result = markdown_module.markdown("This is **bold** text")
        assert "<strong>bold</strong>" in result

    def test_italic_text(self):
        """Test italic text conversion."""
        result = markdown_module.markdown("This is *italic* text")
        assert "<em>italic</em>" in result

    def test_inline_code(self):
        """Test inline code conversion."""
        result = markdown_module.markdown("Use `print()` function")
        assert "<code>print()</code>" in result

    def test_code_blocks(self):
        """Test code block conversion."""
        markdown_text = "```python\nprint('hello')\n```"
        result = markdown_module.markdown(markdown_text)
        assert '<pre><code class="python">\nprint(\'hello\')</code></pre>' in result

    def test_code_blocks_without_language(self):
        """Test code block conversion without language specification."""
        markdown_text = "```\nsome code\n```"
        result = markdown_module.markdown(markdown_text)
        assert '<pre><code class="">\nsome code</code></pre>' in result

    def test_links(self):
        """Test link conversion."""
        result = markdown_module.markdown("[Click here](https://example.com)")
        assert '<a href="https://example.com">Click here</a>' in result

    def test_paragraphs(self):
        """Test paragraph separation."""
        markdown_text = "First paragraph\n\nSecond paragraph"
        result = markdown_module.markdown(markdown_text)
        assert "<p>First paragraph</p><p>Second paragraph</p>" in result

    def test_headers_not_wrapped_in_paragraphs(self):
        """Test that headers are not wrapped in paragraph tags."""
        result = markdown_module.markdown("# Title\n\nSome text")
        # Headers should not have <p> tags around them
        assert "<h1>Title</h1>" in result
        assert "<p><h1>" not in result
        assert "</h1></p>" not in result

    def test_code_blocks_not_wrapped_in_paragraphs(self):
        """Test that code blocks are not wrapped in paragraph tags."""
        markdown_text = "```\ncode here\n```"
        result = markdown_module.markdown(markdown_text)
        assert "<pre>" in result
        assert "<p><pre>" not in result
        assert "</pre></p>" not in result

    def test_complex_markdown(self):
        """Test complex markdown with multiple elements."""
        markdown_text = """# Title

This is a **bold** statement with *italic* text.

Here's some `inline code` and a [link](https://example.com).

```python
# Hello
def hello():
    print("world")
```

## Section

Another paragraph here."""

        result = markdown_module.markdown(markdown_text)

        # Check all elements are present
        assert "<h1>Title</h1>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "<code>inline code</code>" in result
        assert '<a href="https://example.com">link</a>' in result
        assert '<pre><code class="python">' in result
        assert "<h2>Section</h2>" in result
        assert "<h1>Hello</h1>" in result

    def test_empty_string(self):
        """Test handling of empty string."""
        result = markdown_module.markdown("")
        assert "<p></p>" in result

    def test_whitespace_only(self):
        """Test handling of whitespace-only string."""
        result = markdown_module.markdown("   \n   ")
        assert "<p>   \n   </p>" in result

    def test_nested_formatting(self):
        """Test nested bold and italic formatting."""
        result = markdown_module.markdown("***bold and italic***")
        # The function processes ** first, then *, creating nested tags
        assert "<strong><em>bold and italic</strong></em>" in result

    def test_multiple_links_same_line(self):
        """Test multiple links on the same line."""
        markdown_text = "[First link](http://first.com) and [Second link](http://second.com)"
        result = markdown_module.markdown(markdown_text)
        assert '<a href="http://first.com">First link</a>' in result
        assert '<a href="http://second.com">Second link</a>' in result

    def test_header_with_special_characters(self):
        """Test headers containing special characters."""
        result = markdown_module.markdown("# Title with *italic* and **bold**")
        assert "<h1>Title with <em>italic</em> and <strong>bold</strong></h1>" in result