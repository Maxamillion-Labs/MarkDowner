# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""PDF converter."""

from typing import BinaryIO, Optional

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._sandbox import ParserSandboxLimits, run_in_subprocess
from .._stream_info import StreamInfo
from .._temp_utils import materialize_stream_to_temp_path
from .._exceptions import MissingDependencyException


def _extract_pdf_text(pdf_path: str) -> str:
    from pdfminer.high_level import extract_text
    from pdfminer.pdfparser import PDFSyntaxError

    try:
        return extract_text(pdf_path)
    except PDFSyntaxError as exc:
        raise RuntimeError(f"PDF parsing error: {exc}") from exc


class PdfConverter(DocumentConverter):
    """Converter for PDF files."""

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is a PDF file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if mimetype == "application/pdf":
            return True

        if extension == ".pdf":
            return True

        # Check magic bytes
        stream.seek(0)
        magic = stream.read(5)
        stream.seek(0)

        return magic == b"%PDF-"

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert PDF to Markdown."""
        try:
            from pdfminer.high_level import extract_text
            from pdfminer.pdfparser import PDFSyntaxError
        except ImportError:
            raise MissingDependencyException(
                "pdfminer.six is required for PDF conversion. Install with: pip install markdowner[pdf]"
            )
        del extract_text, PDFSyntaxError

        with materialize_stream_to_temp_path(stream, ".pdf") as tmp_path:
            text = run_in_subprocess(
                _extract_pdf_text,
                str(tmp_path),
                limits=ParserSandboxLimits(),
            )

        # Clean up text
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)

        return DocumentConverterResult(text_content=text)
