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

    _CSV_EXTENSIONS = {".csv", ".tsv"}
    _STRONG_CSV_MIME_TYPES = {
        "application/csv",
        "text/csv",
        "text/tab-separated-values",
    }

    def _read_sample(self, stream: BinaryIO, size: int = 4096) -> bytes:
        stream.seek(0)
        chunk = stream.read(size)
        stream.seek(0)
        return chunk

    @staticmethod
    def _looks_like_rtf(chunk: bytes) -> bool:
        normalized = chunk
        if normalized.startswith(b"\xef\xbb\xbf"):
            normalized = normalized[3:]
        return normalized.lstrip().startswith(b"{\\rtf")

    def _sniff_dialect(self, text: str) -> csv.Dialect | None:
        try:
            return csv.Sniffer().sniff(text, delimiters=",;\t|")
        except csv.Error:
            return None

    def _parse_candidate_rows(
        self,
        text: str,
        dialect: csv.Dialect,
    ) -> list[list[str]]:
        rows = []
        for row in csv.reader(io.StringIO(text), dialect):
            if any(cell.strip() for cell in row):
                rows.append(row)
            if len(rows) >= 5:
                break
        return rows

    def _detect_dialect(self, chunk: bytes) -> csv.Dialect | None:
        for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            try:
                text = chunk.decode(encoding)
            except UnicodeDecodeError:
                continue

            dialect = self._sniff_dialect(text)
            if dialect is None:
                continue

            rows = self._parse_candidate_rows(text, dialect)
            if len(rows) < 2:
                continue
            if len(rows[0]) <= 1:
                continue

            return dialect

        return None

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is a CSV file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()
        chunk = self._read_sample(stream)

        if self._looks_like_rtf(chunk):
            return False

        if mimetype in self._STRONG_CSV_MIME_TYPES:
            return True

        if extension in self._CSV_EXTENSIONS:
            return True

        if extension and extension not in self._CSV_EXTENSIONS:
            return False

        return self._detect_dialect(chunk) is not None

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
            "utf-8-sig",
            "cp1252",
            "latin-1",
        ):
            if encoding and encoding not in encodings:
                encodings.append(encoding)

        last_error = None
        for encoding in encodings:
            try:
                decoded = content.decode(encoding)
                dialect = self._sniff_dialect(decoded) or csv.excel
                rows = list(csv.reader(io.StringIO(decoded), dialect))
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
