# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""XLS converter (legacy)."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._limits import DEFAULT_LIMITS, Limits
from .._sandbox import ParserSandboxLimits, run_in_subprocess
from .._stream_info import StreamInfo
from .._temp_utils import materialize_stream_to_temp_path
from .._exceptions import MissingDependencyException


def _convert_xls_to_markdown(xls_path: str) -> str:
    import pandas as pd

    excel_file = pd.ExcelFile(xls_path)
    sheets = []

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        sheets.append(f"## Sheet: {sheet_name}\n")
        sheets.append(df.to_markdown(index=False))
        sheets.append("\n")

    return "\n".join(sheets)


class XlsConverter(DocumentConverter):
    """Converter for legacy XLS files."""

    def __init__(self, limits: Limits = DEFAULT_LIMITS):
        self._limits = limits

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

        return False

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

        try:
            with materialize_stream_to_temp_path(stream, ".xls") as tmp_path:
                text = run_in_subprocess(
                    _convert_xls_to_markdown,
                    str(tmp_path),
                    limits=ParserSandboxLimits(),
                )
        except Exception as e:
            raise RuntimeError(f"XLS conversion failed: {e}") from e

        return DocumentConverterResult(text_content=text)
