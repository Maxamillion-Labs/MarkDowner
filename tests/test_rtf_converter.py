# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test RTF converter."""

import io
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from markdowner import MarkDowner
from markdowner._stream_info import StreamInfo
from markdowner.converters._rtf_converter import RtfConverter
from markdowner._exceptions import MissingDependencyException


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


class TestRtfConverterPandocSuccess:
    """Test RTF converter success path."""

    def test_pandoc_success_returns_markdown(self):
        """Pandoc returning markdown should return DocumentConverterResult."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(b"{\\rtf1\\ansi test}")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"# Hello World"
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = converter.convert(stream, stream_info)

        assert result.text_content == "# Hello World"

    def test_cli_file_flow_converts_rtf(self):
        """CLI file flow should convert RTF to markdown."""
        md = MarkDowner()

        result = md.convert("tests/test_files/sample.rtf")

        assert result.text_content
        assert "{\\rtf" not in result.text_content


class TestRtfConverterPandocMissing:
    """Test RTF converter missing pandoc."""

    def test_pandoc_missing_raises_missing_dependency(self):
        """Missing pandoc should raise MissingDependencyException."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(b"{\\rtf1\\ansi test}")

        with patch("shutil.which", return_value=None):
            with pytest.raises(MissingDependencyException) as exc_info:
                converter.convert(stream, stream_info)

        assert "pandoc" in str(exc_info.value).lower()

    def test_pandoc_not_found_error_raises_missing_dependency(self):
        """FileNotFoundError should raise MissingDependencyException."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(b"{\\rtf1\\ansi test}")

        with patch("shutil.which", return_value="/usr/bin/pandoc"):
            with patch("subprocess.run", side_effect=FileNotFoundError("pandoc")):
                with pytest.raises(MissingDependencyException) as exc_info:
                    converter.convert(stream, stream_info)

        assert "pandoc" in str(exc_info.value).lower()


class TestRtfConverterPandocTimeout:
    """Test RTF converter timeout."""

    def test_pandoc_timeout_returns_error_result(self):
        """Timeout should return controlled failure result."""
        import subprocess
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(b"{\\rtf1\\ansi test}")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""

        with patch("shutil.which", return_value="/usr/bin/pandoc"):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
                result = converter.convert(stream, stream_info)

        assert result.metadata.get("error")
        assert "timeout" in result.metadata["error"].lower()


class TestRtfConverterPandocError:
    """Test RTF converter error handling."""

    def test_pandoc_nonzero_return_returns_error_result(self):
        """Non-zero return code should return controlled failure."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(b"{\\rtf1\\ansi test}")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = b"Error: invalid RTF content"

        with patch("shutil.which", return_value="/usr/bin/pandoc"):
            with patch("subprocess.run", return_value=mock_result):
                result = converter.convert(stream, stream_info)

        assert result.metadata.get("error")
        assert "conversion failed" in result.metadata["error"].lower()

    def test_pandoc_error_stderr_is_truncated(self):
        """Error stderr should be truncated."""
        converter = RtfConverter()
        stream_info = StreamInfo(extension=".rtf")
        stream = io.BytesIO(b"{\\rtf1\\ansi test}")

        long_error = b"x" * 1000
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = long_error

        with patch("shutil.which", return_value="/usr/bin/pandoc"):
            with patch("subprocess.run", return_value=mock_result):
                result = converter.convert(stream, stream_info)

        assert len(result.metadata["error"]) <= 520


class TestRtfCliStdinFlow:
    """Test RTF CLI stdin flow."""

    def test_cli_stdin_flow(self):
        """CLI stdin flow should convert RTF to markdown."""
        import subprocess
        result = subprocess.run(
            ["python", "-m", "markdowner", "-x", ".rtf"],
            input=open("tests/test_files/sample.rtf", "rb").read(),
            capture_output=True,
            cwd=os.getcwd(),
        )

        assert result.returncode == 0
        output = result.stdout.decode("utf-8")
        assert output
        assert "{\\rtf" not in output
