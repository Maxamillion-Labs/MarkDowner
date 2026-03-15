# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""XLSX converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._limits import DEFAULT_LIMITS, Limits
from .._sandbox import ParserSandboxLimits, run_in_subprocess
from .._stream_info import StreamInfo
from .._temp_utils import materialize_stream_to_temp_path
from .._exceptions import MissingDependencyException
from ._zip_package_helpers import zip_has_members


def _convert_xlsx_to_markdown(xlsx_path: str) -> str:
    import pandas as pd

    excel_file = pd.ExcelFile(xlsx_path)
    sheets = []

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        sheets.append(f"## Sheet: {sheet_name}\n")
        sheets.append(df.to_markdown(index=False))
        sheets.append("\n")

    return "\n".join(sheets)


class XlsxConverter(DocumentConverter):
    """Converter for XLSX files."""

    def __init__(self, limits: Limits = DEFAULT_LIMITS):
        self._limits = limits

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
            if "spreadsheetml" in mimetype or "xlsx" in mimetype:
                return True

        if extension != ".xlsx" and "xlsx" not in mimetype:
            return False

        return zip_has_members(
            stream,
            "[Content_Types].xml",
            "xl/workbook.xml",
            max_entries=self._limits.max_zip_metadata_entries,
            max_metadata_bytes=self._limits.max_zip_metadata_scan_bytes,
        )

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

        del pd

        try:
            with materialize_stream_to_temp_path(stream, ".xlsx") as tmp_path:
                text = run_in_subprocess(
                    _convert_xlsx_to_markdown,
                    str(tmp_path),
                    limits=ParserSandboxLimits(),
                )
        except Exception as e:
            raise RuntimeError(f"XLSX conversion failed: {e}") from e

        return DocumentConverterResult(text_content=text)
