# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""DOCX converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._limits import DEFAULT_LIMITS, Limits
from .._sandbox import ParserSandboxLimits, run_in_subprocess
from .._stream_info import StreamInfo
from .._temp_utils import materialize_stream_to_temp_path
from .._exceptions import MissingDependencyException
from ._zip_package_helpers import zip_has_members


def _convert_docx_to_markdown(docx_path: str) -> str:
    import mammoth

    with open(docx_path, "rb") as docx_file:
        return mammoth.convert_to_markdown(docx_file).value


class DocxConverter(DocumentConverter):
    """Converter for DOCX files."""

    def __init__(self, limits: Limits = DEFAULT_LIMITS):
        self._limits = limits

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

        if extension != ".docx" and mimetype:
            return False

        return zip_has_members(
            stream,
            "[Content_Types].xml",
            "word/document.xml",
            max_entries=self._limits.max_zip_metadata_entries,
            max_metadata_bytes=self._limits.max_zip_metadata_scan_bytes,
        )

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

        del mammoth

        try:
            with materialize_stream_to_temp_path(stream, ".docx") as tmp_path:
                text = run_in_subprocess(
                    _convert_docx_to_markdown,
                    str(tmp_path),
                    limits=ParserSandboxLimits(),
                )
        except Exception as e:
            raise RuntimeError(f"DOCX conversion failed: {e}") from e

        return DocumentConverterResult(text_content=text)
