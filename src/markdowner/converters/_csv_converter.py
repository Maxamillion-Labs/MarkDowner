# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""CSV converter."""

import csv
import io
from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo


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
        stream.seek(0)
        content = stream.read()
        warnings = []
        encodings = []
        for encoding in (
            stream_info.charset,
            "utf-8",
            "cp1252",
            "latin-1",
        ):
            if encoding and encoding not in encodings:
                encodings.append(encoding)

        last_error = None
        for encoding in encodings:
            try:
                decoded = content.decode(encoding)
                rows = list(csv.reader(io.StringIO(decoded)))
                if not rows:
                    raise RuntimeError("CSV conversion failed: empty input")
                header = rows[0]
                body = rows[1:]
                separator = ["---"] * len(header)
                markdown_rows = [
                    "| " + " | ".join(header) + " |",
                    "| " + " | ".join(separator) + " |",
                ]
                for row in body:
                    padded_row = row + [""] * (len(header) - len(row))
                    markdown_rows.append("| " + " | ".join(padded_row[: len(header)]) + " |")
                metadata = {"encoding": encoding}
                if stream_info.charset and encoding != stream_info.charset:
                    warnings.append(
                        f"CSV decoded with fallback encoding {encoding} instead of {stream_info.charset}"
                    )
                return DocumentConverterResult(
                    text_content="\n".join(markdown_rows),
                    metadata=metadata,
                    warnings=warnings,
                )
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                break

        raise RuntimeError(f"CSV conversion failed: {last_error}") from last_error
