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
from .._sandbox import ParserSandboxLimits, run_in_subprocess
from .._stream_info import StreamInfo
from .._temp_utils import materialize_stream_to_temp_path


def _convert_html_to_markdown(html_path: str, charset: str | None) -> str:
    with open(html_path, "rb") as fh:
        content = fh.read()

    try:
        decoded = content.decode(charset or "utf-8", errors="replace")
    except Exception:
        decoded = content.decode("utf-8", errors="replace")

    soup = BeautifulSoup(decoded, "html.parser")

    for element in soup(["script", "style"]):
        element.decompose()

    return to_markdown(
        str(soup),
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
        autolinks=True,
        strong_em_symbol="*",
    ).strip()


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
        try:
            with materialize_stream_to_temp_path(stream, ".html") as tmp_path:
                text = run_in_subprocess(
                    _convert_html_to_markdown,
                    str(tmp_path),
                    stream_info.charset,
                    limits=ParserSandboxLimits(),
                )
        except Exception as exc:
            raise RuntimeError(f"HTML conversion failed: {exc}") from exc

        return DocumentConverterResult(text_content=text)
