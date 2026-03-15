# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""PPTX converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException


class PptxConverter(DocumentConverter):
    """Converter for PPTX files."""

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is a PPTX file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if "presentation" in mimetype or "powerpoint" in mimetype:
            return True

        if extension in (".pptx",):
            return True

        # Check ZIP magic
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
        """Convert PPTX to Markdown."""
        try:
            from pptx import Presentation
        except ImportError:
            raise MissingDependencyException(
                "python-pptx is required for PPTX conversion. Install with: pip install markdowner[pptx]"
            )

        # Save to temp file
        import tempfile
        import os

        stream.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp.write(stream.read())
            tmp_path = tmp.name

        try:
            prs = Presentation(tmp_path)
            slides = []

            for i, slide in enumerate(prs.slides, 1):
                slides.append(f"## Slide {i}\n")

                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        slides.append(shape.text)
                        slides.append("\n")

            text = "\n".join(slides)
        except Exception as e:
            return DocumentConverterResult(
                text_content="",
                metadata={"error": str(e)},
                warnings=[f"PPTX conversion failed: {e}"],
            )
        finally:
            os.unlink(tmp_path)

        return DocumentConverterResult(text_content=text)