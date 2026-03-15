# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""PDF converter."""

from typing import BinaryIO, Optional

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException


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

        # Save to temp file (pdfminer requires a file path)
        import tempfile
        import os

        stream.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(stream.read())
            tmp_path = tmp.name

        try:
            try:
                text = extract_text(tmp_path)
            except PDFSyntaxError as e:
                return DocumentConverterResult(
                    text_content="",
                    metadata={"error": f"PDF parsing error: {e}"},
                    warnings=["PDF could not be parsed"],
                )
        finally:
            os.unlink(tmp_path)

        # Clean up text
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)

        return DocumentConverterResult(text_content=text)