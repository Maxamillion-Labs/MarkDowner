# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Plain text converter."""

import io
from typing import BinaryIO

from .._base_converter import (
    DocumentConverter,
    DocumentConverterResult,
    PRIORITY_GENERIC_FILE_FORMAT,
)
from .._stream_info import StreamInfo


class PlainTextConverter(DocumentConverter):
    """Converter for plain text files."""

    priority = PRIORITY_GENERIC_FILE_FORMAT

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is a plain text file."""
        mimetype = stream_info.mimetype or ""
        stream.seek(0)
        chunk = stream.read(4096)
        stream.seek(0)

        if b"\x00" in chunk:
            return False

        # Check MIME type
        if mimetype.startswith("text/"):
            return True

        extension = (stream_info.extension or "").lower()

        # Check extension
        text_extensions = {".txt", ".text", ".log", ".ini", ".cfg", ".conf", ".json", ".xml", ".yaml", ".yml", ".toml", ".md", ".markdown"}
        if extension in text_extensions:
            return True

        # Try to detect if it's text
        stream.seek(0)
        try:
            # Try to decode as text
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    chunk.decode(encoding)
                    return True
                except (UnicodeDecodeError, UnicodeError):
                    continue

            return False
        except Exception:
            return False

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert plain text to Markdown."""
        # Determine encoding
        charset = stream_info.charset or "utf-8"

        # Try to detect encoding if not specified
        if stream_info.charset is None:
            stream.seek(0)
            chunk = stream.read(4096)
            stream.seek(0)

            import charset_normalizer
            result = charset_normalizer.from_bytes(chunk).best()
            if result:
                charset = result.encoding
            else:
                charset = "utf-8"

        # Read content
        stream.seek(0)
        try:
            content = stream.read().decode(charset, errors="replace")
        except Exception:
            # Fallback to UTF-8
            stream.seek(0)
            content = stream.read().decode("utf-8", errors="replace")

        # Escape special Markdown characters
        content = self._escape_markdown(content)

        return DocumentConverterResult(text_content=content)

    def _escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters that could cause issues."""
        # Only escape in code blocks where it matters most
        # For regular text, we don't need to escape everything
        return text
