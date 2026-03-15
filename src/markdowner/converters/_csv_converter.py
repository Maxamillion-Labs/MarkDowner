# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""CSV converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException


class CsvConverter(DocumentConverter):
    """Converter for CSV files."""

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is a CSV file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if mimetype == "text/csv" or "csv" in mimetype:
            return True

        if extension in (".csv",):
            return True

        # Check content for CSV-like structure
        stream.seek(0)
        chunk = stream.read(4096)
        stream.seek(0)

        try:
            text = chunk.decode("utf-8", errors="ignore")
            # Simple heuristic: contains commas and newlines
            if "," in text and "\n" in text:
                return True
        except Exception:
            pass

        return False

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert CSV to Markdown."""
        try:
            import pandas as pd
        except ImportError:
            raise MissingDependencyException(
                "pandas is required for CSV conversion. Install with: pip install markdowner[xlsx]"
            )

        # Determine encoding
        charset = stream_info.charset or "utf-8"

        stream.seek(0)
        try:
            content = stream.read().decode(charset, errors="replace")
        except Exception:
            stream.seek(0)
            content = stream.read().decode("utf-8", errors="replace")

        # Save to temp file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            df = pd.read_csv(tmp_path)
            text = df.to_markdown(index=False)
        except Exception as e:
            return DocumentConverterResult(
                text_content="",
                metadata={"error": str(e)},
                warnings=[f"CSV conversion failed: {e}"],
            )
        finally:
            os.unlink(tmp_path)

        return DocumentConverterResult(text_content=text)