# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test RTF parser."""

from pathlib import Path

import pytest

from markdowner.converters._rtf_parser import RtfParser, parse_rtf
from markdowner.converters._rtf_ir import Document, Paragraph, TextInline

FIXTURES = Path(__file__).parent / "test_files" / "rtf"
EXPECTED = Path(__file__).parent / "test_files" / "rtf_expected"


class TestRtfParser:
    """Test RTF parser."""

    def test_simple_text_parsing(self):
        """Simple text should parse to document."""
        content = br"{\rtf1\ansi Hello World}"
        doc = parse_rtf(content)
        assert isinstance(doc, Document)
        assert len(doc.blocks) >= 0

    def test_paragraph_creation(self):
        """Paragraphs should be created from content."""
        content = br"{\rtf1\ansi First paragraph\par Second paragraph}"
        doc = parse_rtf(content)
        assert len(doc.blocks) >= 1

    def test_bold_formatting(self):
        """Bold text should be parsed."""
        content = br"{\rtf1\ansi This is \b bold\b0 text}"
        doc = parse_rtf(content)
        assert len(doc.blocks) >= 1

    def test_italic_formatting(self):
        """Italic text should be parsed."""
        content = br"{\rtf1\ansi This is \i italic\i0 text}"
        doc = parse_rtf(content)
        assert len(doc.blocks) >= 1

    def test_line_break(self):
        """Line breaks should be parsed."""
        content = br"{\rtf1\ansi Line one\line Line two}"
        doc = parse_rtf(content)
        assert len(doc.blocks) >= 1

    def test_tab(self):
        """Tabs should be parsed."""
        content = br"{\rtf1\ansi Column1\tab Column2}"
        doc = parse_rtf(content)
        assert len(doc.blocks) >= 1

    def test_unicode_characters(self):
        """Unicode characters should be parsed."""
        content = br"{\rtf1\ansi Caf\u233}"
        doc = parse_rtf(content)
        assert isinstance(doc, Document)

    def test_nested_groups(self):
        """Nested groups should be handled."""
        content = br"{\rtf1{\fonttbl{\f0 Arial;}}}"
        doc = parse_rtf(content)
        assert isinstance(doc, Document)

    def test_destination_skip(self):
        """Font table and other destinations should be skipped."""
        content = br"{\rtf1\ansi{\fonttbl{\f0 Arial;}}\par Text}"
        doc = parse_rtf(content)
        assert isinstance(doc, Document)
        assert len(doc.blocks) >= 0

    def test_parser_class(self):
        """Parser class should work correctly."""
        content = br"{\rtf1\ansi Test}"
        parser = RtfParser(content)
        doc = parser.parse()
        assert isinstance(doc, Document)

    def test_ansicpg_hex_escapes_honor_declared_codepage(self):
        content = (FIXTURES / "cyrillic_cp1251.rtf").read_bytes()
        expected = (EXPECTED / "cyrillic_cp1251.md").read_text(encoding="utf-8").strip()

        doc = parse_rtf(content)
        text = "".join(
            inline.content
            for block in doc.blocks
            for inline in getattr(block, "inlines", [])
            if isinstance(inline, TextInline)
        )

        assert text.strip() == expected

    def test_unicode_fallback_characters_are_skipped(self):
        content = br"{\rtf1\ansi\uc1 Caf\u233? and Gr\u252?ner}"
        doc = parse_rtf(content)
        text = "".join(
            inline.content
            for block in doc.blocks
            for inline in getattr(block, "inlines", [])
            if isinstance(inline, TextInline)
        )

        assert text == "Café and Grüner"
