# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""XLS converter (legacy)."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException


class XlsConverter(DocumentConverter):
    """Converter for legacy XLS files."""

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is an XLS file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if "spreadsheet" in mimetype or "excel" in mimetype:
            if "xls" in mimetype and "xlsx" not in mimetype:
                return True

        if extension == ".xls":
            return True

        # Check OLE magic
        stream.seek(0)
        magic = stream.read(8)
        stream.seek(0)

        return magic[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert XLS to Markdown."""
        try:
            import pandas as pd
        except ImportError:
            raise MissingDependencyException(
                "pandas is required for XLS conversion. Install with: pip install markdowner[xls]"
            )

        # Save to temp file
        import tempfile
        import os

        stream.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as tmp:
            tmp.write(stream.read())
            tmp_path = tmp.name

        try:
            excel_file = pd.ExcelFile(tmp_path)
            sheets = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets.append(f"## Sheet: {sheet_name}\n")
                sheets.append(df.to_markdown(index=False))
                sheets.append("\n")

            text = "\n".join(sheets)
        except Exception as e:
            raise RuntimeError(f"XLS conversion failed: {e}") from e
        finally:
            os.unlink(tmp_path)

        return DocumentConverterResult(text_content=text)
