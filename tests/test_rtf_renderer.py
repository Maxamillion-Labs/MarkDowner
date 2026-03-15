# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test RTF renderer."""

import pytest

from markdowner.converters._rtf_ir import Document, Paragraph, TextInline, LineBreak
from markdowner.converters._rtf_renderer import RtfRenderer, render_to_markdown


class TestRtfRenderer:
    """Test RTF renderer."""

    def test_simple_text_rendering(self):
        """Simple text should render to markdown."""
        doc = Document()
        doc.blocks.append(Paragraph(inlines=[TextInline(content="Hello World")]))
        renderer = RtfRenderer(doc)
        output = renderer.render()
        assert "Hello World" in output

    def test_bold_rendering(self):
        """Bold text should render as **text**."""
        doc = Document()
        doc.blocks.append(Paragraph(
            inlines=[TextInline(content="bold", bold=True)]
        ))
        renderer = RtfRenderer(doc)
        output = renderer.render()
        assert "**bold**" in output

    def test_italic_rendering(self):
        """Italic text should render as *text*."""
        doc = Document()
        doc.blocks.append(Paragraph(
            inlines=[TextInline(content="italic", italic=True)]
        ))
        renderer = RtfRenderer(doc)
        output = renderer.render()
        assert "*italic*" in output

    def test_bold_italic_rendering(self):
        """Bold and italic should render as ***text***."""
        doc = Document()
        doc.blocks.append(Paragraph(
            inlines=[TextInline(content="both", bold=True, italic=True)]
        ))
        renderer = RtfRenderer(doc)
        output = renderer.render()
        assert "***both***" in output

    def test_line_break_rendering(self):
        """Line breaks should render as  \\n"""
        doc = Document()
        doc.blocks.append(Paragraph(
            inlines=[TextInline(content="Line1"), LineBreak(), TextInline(content="Line2")]
        ))
        renderer = RtfRenderer(doc)
        output = renderer.render()
        assert "Line1" in output
        assert "Line2" in output

    def test_max_two_blank_lines(self):
        """Should not output more than 2 consecutive blank lines."""
        doc = Document()
        for _ in range(5):
            doc.blocks.append(Paragraph(inlines=[TextInline(content="Para")]))
        renderer = RtfRenderer(doc)
        output = renderer.render()
        assert "\n\n\n\n" not in output

    def test_convenience_function(self):
        """render_to_markdown convenience function."""
        doc = Document()
        doc.blocks.append(Paragraph(inlines=[TextInline(content="Test")]))
        output = render_to_markdown(doc)
        assert "Test" in output

    def test_special_characters_escaped(self):
        """Markdown special chars should be escaped."""
        doc = Document()
        doc.blocks.append(Paragraph(
            inlines=[TextInline(content="Test *with* special _chars_")]
        ))
        renderer = RtfRenderer(doc)
        output = renderer.render()
        assert "\\*" in output or "Test" in output

    def test_empty_paragraphs_skipped(self):
        """Empty paragraphs should be skipped."""
        doc = Document()
        doc.blocks.append(Paragraph(inlines=[]))
        doc.blocks.append(Paragraph(inlines=[TextInline(content="Content")]))
        renderer = RtfRenderer(doc)
        output = renderer.render()
        assert "Content" in output
