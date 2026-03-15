# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test conversion parity - verify local converters work."""

import io
import tempfile
import os
import zipfile
from unittest.mock import patch

import pytest

from markdowner import MarkDowner
from markdowner._stream_info import StreamInfo
from markdowner.converters._image_converter import ImageConverter, _EXIFTOOL_SUCCESS_CACHE


class TestPlainTextConversion:
    """Test plain text conversion."""

    def test_convert_simple_text(self):
        """Simple text should convert."""
        md = MarkDowner()
        content = b"Hello, World!"
        result = md.convert(io.BytesIO(content))
        assert "Hello, World!" in result.text_content

    def test_convert_text_file(self):
        """Text file should convert."""
        md = MarkDowner()

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
            tmp.write("Test content")
            tmp_path = tmp.name

        try:
            result = md.convert(tmp_path)
            assert "Test content" in result.text_content
        finally:
            os.unlink(tmp_path)


class TestHtmlConversion:
    """Test HTML conversion."""

    def test_convert_simple_html(self):
        """Simple HTML should convert."""
        md = MarkDowner()
        html = (
            b"<html><body><h1>Title</h1><p><a href='https://example.com'>Link</a></p>"
            b"<ul><li>First</li><li>Second</li></ul><script>alert(1)</script></body></html>"
        )
        stream_info = StreamInfo(extension=".html")
        result = md.convert(io.BytesIO(html), stream_info=stream_info)
        assert "# Title" in result.text_content
        assert "[Link](https://example.com)" in result.text_content
        assert "- First" in result.text_content
        assert "alert(1)" not in result.text_content


class TestZipConversion:
    """Test ZIP conversion."""

    def test_convert_simple_zip(self):
        """Simple ZIP should convert."""
        md = MarkDowner()

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zf:
                zf.writestr("test.txt", "File content")
            tmp_path = tmp.name

        try:
            result = md.convert(tmp_path)
            assert "test.txt" in result.text_content
            assert "File content" in result.text_content
            assert result.metadata.get("files_processed", 0) == 1
        finally:
            os.unlink(tmp_path)

    def test_zip_conversion_is_deterministic_and_warns_for_unsupported_entries(self):
        """ZIP conversion should sort entries and warn for unsupported inner files."""
        md = MarkDowner()
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("b.txt", "second")
            zf.writestr("a.txt", "first")
            zf.writestr("image.bin", b"\x00\x01\x02\x03")

        result = md.convert(io.BytesIO(archive.getvalue()), stream_info=StreamInfo(extension=".zip"))

        assert result.text_content.index("## a.txt") < result.text_content.index("## b.txt")
        assert "first" in result.text_content
        assert any("unsupported zip entry: image.bin" in warning.lower() for warning in result.warnings)


class TestImageConversion:
    """Test image conversion."""

    def setup_method(self):
        _EXIFTOOL_SUCCESS_CACHE.clear()

    @staticmethod
    def _png_bytes() -> bytes:
        return (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
            b"\x90wS\xde\x00\x00\x00\x0cIDAT\x08\x99c``\x00\x00\x00\x04\x00\x01"
            b"\x0b\xe7\x02\x9d\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    def test_exiftool_valid_version_extracts_metadata(self):
        converter = ImageConverter()

        with patch("markdowner.converters._image_converter.subprocess.run") as run_mock:
            run_mock.side_effect = [
                type("Result", (), {"returncode": 0, "stdout": "12.90\n"})(),
                type("Result", (), {"returncode": 0, "stdout": '[{"ImageWidth": 1}]'})(),
            ]
            result = converter.convert(
                io.BytesIO(self._png_bytes()),
                StreamInfo(extension=".png", filename="test.png"),
                exiftool_path="/usr/bin/exiftool",
            )

        assert result.metadata["exif"]["ImageWidth"] == 1
        assert run_mock.call_count == 2

    def test_exiftool_invalid_version_output_warns(self):
        converter = ImageConverter()

        with patch("markdowner.converters._image_converter.subprocess.run") as run_mock:
            run_mock.return_value = type("Result", (), {"returncode": 0, "stdout": "not-a-version"})()
            result = converter.convert(
                io.BytesIO(self._png_bytes()),
                StreamInfo(extension=".png", filename="test.png"),
                exiftool_path="/usr/bin/exiftool",
            )

        assert any("invalid exiftool version" in warning.lower() for warning in result.warnings)

    def test_exiftool_missing_binary_warns(self):
        converter = ImageConverter()

        with patch(
            "markdowner.converters._image_converter.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            result = converter.convert(
                io.BytesIO(self._png_bytes()),
                StreamInfo(extension=".png", filename="test.png"),
                exiftool_path="/missing/exiftool",
            )

        assert any("executable not found" in warning.lower() for warning in result.warnings)

    def test_exiftool_vulnerable_version_warns(self):
        converter = ImageConverter()

        with patch("markdowner.converters._image_converter.subprocess.run") as run_mock:
            run_mock.return_value = type("Result", (), {"returncode": 0, "stdout": "12.23\n"})()
            result = converter.convert(
                io.BytesIO(self._png_bytes()),
                StreamInfo(extension=".png", filename="test.png"),
                exiftool_path="/usr/bin/exiftool",
            )

        assert any("below the minimum supported 12.24" in warning for warning in result.warnings)


class TestCsvConversion:
    """Test CSV conversion."""

    def test_convert_simple_csv(self):
        """Simple CSV should convert."""
        md = MarkDowner()
        csv = b"a,b,c\n1,2,3\n4,5,6"
        stream_info = StreamInfo(extension=".csv")
        result = md.convert(io.BytesIO(csv), stream_info=stream_info)
        assert "a" in result.text_content
        assert "1" in result.text_content


class TestExtensionInference:
    """Test extension inference from filename."""

    def test_extension_from_path(self):
        """Extension should be inferred from path."""
        md = MarkDowner()

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"content")
            tmp_path = tmp.name

        try:
            result = md.convert(tmp_path)
            assert "content" in result.text_content
        finally:
            os.unlink(tmp_path)


class TestMimetypeHints:
    """Test MIME type hints."""

    def test_mimetype_hint(self):
        """MIME type hint should work."""
        md = MarkDowner()
        content = b"Test content"
        stream_info = StreamInfo(mimetype="text/plain")
        result = md.convert(io.BytesIO(content), stream_info=stream_info)
        assert "Test content" in result.text_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
