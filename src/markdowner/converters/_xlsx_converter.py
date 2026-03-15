# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""XLSX converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException


class XlsxConverter(DocumentConverter):
    """Converter for XLSX files."""

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is an XLSX file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if "spreadsheet" in mimetype or "excel" in mimetype:
            if "xlsx" in mimetype:
                return True

        if extension in (".xlsx",):
            return True

        if extension not in (".xlsx",) and "xlsx" not in mimetype:
            return False

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
        """Convert XLSX to Markdown."""
        try:
            import pandas as pd
        except ImportError:
            raise MissingDependencyException(
                "pandas is required for XLSX conversion. Install with: pip install markdowner[xlsx]"
            )

        # Save to temp file
        import tempfile
        import os

        stream.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(stream.read())
            tmp_path = tmp.name

        try:
            # Read all sheets
            excel_file = pd.ExcelFile(tmp_path)
            sheets = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets.append(f"## Sheet: {sheet_name}\n")
                sheets.append(df.to_markdown(index=False))
                sheets.append("\n")

            text = "\n".join(sheets)
        except Exception as e:
            return DocumentConverterResult(
                text_content="",
                metadata={"error": str(e)},
                warnings=[f"XLSX conversion failed: {e}"],
            )
        finally:
            os.unlink(tmp_path)

        return DocumentConverterResult(text_content=text)