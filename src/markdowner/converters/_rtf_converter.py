# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""RTF converter using pandoc."""

import subprocess
from typing import BinaryIO

from .._base_converter import (
    DocumentConverter,
    DocumentConverterResult,
    PRIORITY_SPECIFIC_FILE_FORMAT,
)
from .._exceptions import MissingDependencyException
from .._stream_info import StreamInfo


class RtfConverter(DocumentConverter):
    """Converter for RTF files using pandoc."""

    priority = PRIORITY_SPECIFIC_FILE_FORMAT
    DEFAULT_TIMEOUT = 30

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is an RTF file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if extension == ".rtf":
            return True

        if mimetype in ("text/rtf", "application/rtf"):
            return True

        stream.seek(0)
        chunk = stream.read(8)
        stream.seek(0)

        if chunk.startswith(b"{\\rtf"):
            return True

        return False

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert RTF to Markdown using pandoc."""
        import shutil

        pandoc_path = shutil.which("pandoc")
        if pandoc_path is None:
            raise MissingDependencyException(
                "pandoc is required for RTF conversion. Install with: brew install pandoc"
            )

        stream.seek(0)
        rtf_content = stream.read()
        stream.seek(0)

        try:
            result = subprocess.run(
                [
                    pandoc_path,
                    "-f", "rtf",
                    "-t", "gfm",
                    "--wrap=none",
                    "--markdown-headings=atx",
                ],
                input=rtf_content,
                capture_output=True,
                timeout=self.DEFAULT_TIMEOUT,
                check=False,
            )
        except FileNotFoundError:
            raise MissingDependencyException(
                "pandoc is required for RTF conversion. Install with: brew install pandoc"
            )
        except subprocess.TimeoutExpired:
            return DocumentConverterResult(
                text_content="",
                metadata={"error": "RTF conversion timed out (timeout)"},
            )

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            truncated_stderr = stderr[:497] if len(stderr) > 497 else stderr
            return DocumentConverterResult(
                text_content="",
                metadata={"error": f"RTF conversion failed: {truncated_stderr}"},
            )

        markdown_content = result.stdout.decode("utf-8", errors="replace")

        return DocumentConverterResult(text_content=markdown_content)
