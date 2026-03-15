# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""HTML converter."""

from typing import BinaryIO

from bs4 import BeautifulSoup
from markdownify import markdownify as to_markdown

from .._base_converter import (
    DocumentConverter,
    DocumentConverterResult,
    PRIORITY_GENERIC_FILE_FORMAT,
)
from .._stream_info import StreamInfo


class HtmlConverter(DocumentConverter):
    """Converter for HTML files."""

    priority = PRIORITY_GENERIC_FILE_FORMAT

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is an HTML file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        # Check MIME type
        if mimetype in ("text/html", "application/xhtml+xml"):
            return True

        # Check extension
        if extension in (".html", ".htm", ".xhtml"):
            return True

        # Try to detect from content
        stream.seek(0)
        chunk = stream.read(4096)
        stream.seek(0)

        # Look for HTML tags
        try:
            text = chunk.decode("utf-8", errors="ignore")
            if "<html" in text.lower() or "<!doctype" in text.lower():
                return True
        except Exception:
            pass

        return False

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert HTML to Markdown."""
        # Determine encoding
        charset = stream_info.charset or "utf-8"

        # Read content
        stream.seek(0)
        try:
            content = stream.read().decode(charset, errors="replace")
        except Exception:
            stream.seek(0)
            content = stream.read().decode("utf-8", errors="replace")

        # Parse HTML
        soup = BeautifulSoup(content, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        text = to_markdown(
            str(soup),
            heading_style="ATX",
            bullets="-",
            strip=["script", "style"],
        ).strip()

        return DocumentConverterResult(text_content=text)
