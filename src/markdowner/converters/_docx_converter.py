# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""DOCX converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException


class DocxConverter(DocumentConverter):
    """Converter for DOCX files."""

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is a DOCX file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if mimetype in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",):
            return True

        if extension == ".docx":
            return True

        # Check ZIP magic (docx is a zip)
        stream.seek(0)
        magic = stream.read(2)
        stream.seek(0)

        return magic == b"PK"

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert DOCX to Markdown."""
        try:
            import mammoth
        except ImportError:
            raise MissingDependencyException(
                "mammoth is required for DOCX conversion. Install with: pip install markdowner[docx]"
            )

        # Save to temp file
        import tempfile
        import os

        stream.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(stream.read())
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as docx_file:
                result = mammoth.convert_to_markdown(docx_file)
                text = result.value
        except Exception as e:
            return DocumentConverterResult(
                text_content="",
                metadata={"error": str(e)},
                warnings=[f"DOCX conversion failed: {e}"],
            )
        finally:
            os.unlink(tmp_path)

        return DocumentConverterResult(text_content=text)