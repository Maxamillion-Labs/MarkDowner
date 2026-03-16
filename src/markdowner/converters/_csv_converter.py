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
    _SNIFF_SAMPLE_BYTES = 8192
    _MAX_ROWS = 10000
    _MAX_COLUMNS = 256
    _MAX_FIELD_CHARS = 16384
    _STRONG_CSV_MIME_TYPES = {
        "application/csv",
        "text/csv",
        "text/tab-separated-values",
    }

    def _read_sample(self, stream: BinaryIO, size: int = _SNIFF_SAMPLE_BYTES) -> bytes:
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

    def _validate_row(self, row: list[str]) -> None:
        if len(row) > self._MAX_COLUMNS:
            raise RuntimeError(
                f"CSV conversion failed: row has {len(row)} columns, limit is {self._MAX_COLUMNS}"
            )
        for field in row:
            if len(field) > self._MAX_FIELD_CHARS:
                raise RuntimeError(
                    "CSV conversion failed: field exceeds maximum allowed size"
                )

    def _convert_with_encoding(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        encoding: str,
    ) -> DocumentConverterResult:
        stream.seek(0)
        text_stream = io.TextIOWrapper(stream, encoding=encoding, errors="strict", newline="")
        try:
            sniff_sample = text_stream.read(self._SNIFF_SAMPLE_BYTES)
            text_stream.seek(0)
            dialect = self._sniff_dialect(sniff_sample) or csv.excel
            reader = csv.reader(text_stream, dialect)
            markdown_rows: list[str] = []
            header: list[str] | None = None
            row_count = 0

            for row in reader:
                if not any(cell.strip() for cell in row):
                    continue

                row_count += 1
                if row_count > self._MAX_ROWS:
                    raise RuntimeError(
                        f"CSV conversion failed: row count exceeds {self._MAX_ROWS}"
                    )

                self._validate_row(row)

                if header is None:
                    header = row
                    separator = ["---"] * len(header)
                    markdown_rows.append("| " + " | ".join(header) + " |")
                    markdown_rows.append("| " + " | ".join(separator) + " |")
                    continue

                padded_row = row + [""] * (len(header) - len(row))
                markdown_rows.append("| " + " | ".join(padded_row[: len(header)]) + " |")

            if header is None:
                raise RuntimeError("CSV conversion failed: empty input")

            warnings = []
            if stream_info.charset and encoding != stream_info.charset:
                warnings.append(
                    f"CSV decoded with fallback encoding {encoding} instead of {stream_info.charset}"
                )

            return DocumentConverterResult(
                text_content="\n".join(markdown_rows),
                metadata={"encoding": encoding, "rows": row_count, "columns": len(header)},
                warnings=warnings,
            )
        finally:
            text_stream.detach()

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
                return self._convert_with_encoding(stream, stream_info, encoding)
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                break

        raise RuntimeError(f"CSV conversion failed: {last_error}") from last_error
