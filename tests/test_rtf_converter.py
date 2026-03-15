# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test RTF converter - native implementation."""

import io

import pytest

from markdowner import MarkDowner
from markdowner._base_converter import DocumentConverterResult
from markdowner._stream_info import StreamInfo
from markdowner.converters._csv_converter import CsvConverter
from markdowner.converters._rtf_converter import RtfConverter


RTF_CSV_LIKE_SAMPLE = (
    b"{\\rtf1\\ansi\\deff0\n"
    b"{\\fonttbl{\\f0 Arial;}}\n"
    b"\\fs24\n"
    b"Executive Summary, Revenue, Margin\\par\n"
    b"Q1, up 12 percent, stable outlook.\\par\n"
    b"Q2, up 9 percent, hiring freeze.\\par\n"
    b"Risks, inflation, currency volatility, vendor concentration.\\par\n"
    b"}\n"
)

SIMPLE_RTF = br"{\rtf1\ansi Hello World}"

BOLD_RTF = br"{\rtf1\ansi This is \b bold\b0 text}"

ITALIC_RTF = br"{\rtf1\ansi This is \i italic\i0 text}"


class TestRtfConverterAccepts:
    """Test RTF converter accepts logic."""

    def test_accepts_by_extension(self):
        """RTF extension should route to RTF converter."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(b"test content")

        assert converter.accepts(stream, stream_info) is True

    def test_accepts_by_mime_text_rtf(self):
        """text/rtf mime type should be accepted."""
        converter = RtfConverter()
        stream_info = StreamInfo(mimetype="text/rtf")
        stream = io.BytesIO(b"test content")

        assert converter.accepts(stream, stream_info) is True

    def test_accepts_by_mime_application_rtf(self):
        """application/rtf mime type should be accepted."""
        converter = RtfConverter()
        stream_info = StreamInfo(mimetype="application/rtf")
        stream = io.BytesIO(b"test content")

        assert converter.accepts(stream, stream_info) is True

    def test_accepts_by_magic_header(self):
        """Stream beginning with {\\rtf should be accepted."""
        converter = RtfConverter()
        stream_info = StreamInfo()
        stream = io.BytesIO(b"{\\rtf1\\ansi test content")

        assert converter.accepts(stream, stream_info) is True

    def test_accepts_by_magic_header_with_bom_and_whitespace(self):
        """RTF header detection should tolerate BOM and leading whitespace."""
        converter = RtfConverter()
        stream_info = StreamInfo()
        stream = io.BytesIO(b"\xef\xbb\xbf  \n\t{\\rtf1\\ansi test content")

        assert converter.accepts(stream, stream_info) is True


class TestRtfConverterNative:
    """Test RTF native converter functionality."""

    def test_simple_conversion(self):
        """Simple RTF should convert without error."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(SIMPLE_RTF)

        result = converter.convert(stream, stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert result.text_content
        assert "Hello World" in result.text_content

    def test_output_no_raw_rtf(self):
        """Output should not contain raw RTF control text."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(SIMPLE_RTF)

        result = converter.convert(stream, stream_info)

        assert "{\\rtf" not in result.text_content
        assert "\\par" not in result.text_content

    def test_bold_renders_correctly(self):
        """Bold text should render as **text**."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(BOLD_RTF)

        result = converter.convert(stream, stream_info)

        assert "**bold**" in result.text_content

    def test_italic_renders_correctly(self):
        """Italic text should render as *text*."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(ITALIC_RTF)

        result = converter.convert(stream, stream_info)

        assert "*italic*" in result.text_content

    def test_metadata_has_native_converter(self):
        """Result metadata should indicate native converter."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(SIMPLE_RTF)

        result = converter.convert(stream, stream_info)

        assert result.metadata.get("converter") == "native-rtf"

    def test_no_csv_table_artifact(self):
        """No CSV table artifact for RTF content."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(RTF_CSV_LIKE_SAMPLE)

        result = converter.convert(stream, stream_info)

        assert not result.text_content.startswith("| {\\rtf")
        assert "| {\\rtf" not in result.text_content

    def test_malformed_rtf_yields_error_result(self):
        """Malformed RTF should yield controlled error, not crash."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(b"not valid rtf at all {")

        result = converter.convert(stream, stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert result.text_content == ""
        assert "error" in result.metadata


class TestRtfRoutingRegression:
    """Regression coverage for RTF vs CSV routing."""

    def test_csv_converter_rejects_rtf_signature(self):
        """CSV converter should reject obvious RTF payloads."""
        converter = CsvConverter()
        stream_info = StreamInfo(extension=".rtf")

        assert converter.accepts(io.BytesIO(RTF_CSV_LIKE_SAMPLE), stream_info) is False

    def test_explicit_rtf_extension_routes_to_rtf(self):
        """RTF routing should use native converter."""
        md = MarkDowner()
        stream_info = StreamInfo(extension=".rtf")

        result = md.convert(io.BytesIO(SIMPLE_RTF), stream_info=stream_info)

        assert "Hello World" in result.text_content

    def test_csv_fixture_still_converts(self):
        """Real CSV fixtures should still produce markdown tables."""
        md = MarkDowner()

        result = md.convert("tests/test_files/sample.csv")

        assert result.text_content.startswith("| name | score |")
        assert "Alice" in result.text_content


class TestRtfCliFlow:
    """Test RTF CLI flow."""

    def test_cli_file_flow_converts_rtf(self):
        """CLI file flow should convert RTF to markdown."""
        md = MarkDowner()

        result = md.convert("tests/test_files/rtf/simple.rtf")

        assert result.text_content
        assert "{\\rtf" not in result.text_content
