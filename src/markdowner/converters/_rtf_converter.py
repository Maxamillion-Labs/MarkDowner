# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""RTF converter using native parser."""

from typing import BinaryIO

from .._base_converter import (
    DocumentConverter,
    DocumentConverterResult,
    PRIORITY_RTF,
)
from .._stream_info import StreamInfo
from ._rtf_parser import RtfParser
from ._rtf_renderer import RtfRenderer


class RtfConverter(DocumentConverter):
    """Converter for RTF files using native parser."""

    priority = PRIORITY_RTF

    @staticmethod
    def _has_rtf_header(chunk: bytes) -> bool:
        if chunk.startswith(b"\xef\xbb\xbf"):
            chunk = chunk[3:]
        return chunk.lstrip().startswith(b"{\\rtf")

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
        chunk = stream.read(64)
        stream.seek(0)

        if self._has_rtf_header(chunk):
            return True

        return False

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert RTF to Markdown using native parser."""
        stream.seek(0)
        rtf_content = stream.read()

        if not self._has_rtf_header(rtf_content[:256]):
            return DocumentConverterResult(
                text_content="",
                metadata={"error": "RTF native conversion failed: invalid RTF header"},
            )

        try:
            parser = RtfParser(rtf_content)
            doc = parser.parse()
            renderer = RtfRenderer(doc)
            markdown_content = renderer.render()

            return DocumentConverterResult(
                text_content=markdown_content,
                metadata={"converter": "native-rtf"},
            )

        except Exception as e:
            return DocumentConverterResult(
                text_content="",
                metadata={
                    "error": f"RTF native conversion failed: {type(e).__name__}: {str(e)}"
                },
            )
