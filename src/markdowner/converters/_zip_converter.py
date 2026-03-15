# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""ZIP converter with security limits."""

import io
import os
import zipfile
from typing import BinaryIO, List

from .._base_converter import (
    DocumentConverter,
    DocumentConverterResult,
    PRIORITY_GENERIC_FILE_FORMAT,
)
from .._exceptions import (
    FileConversionException,
    UnsupportedFormatException,
    ZipLimitExceededException,
)
from .._limits import Limits, DEFAULT_LIMITS
from .._stream_info import StreamInfo


class ZipConverter(DocumentConverter):
    """Converter for ZIP archives with recursive conversion."""

    priority = PRIORITY_GENERIC_FILE_FORMAT

    def __init__(self, markdowner=None, limits: Limits = None):
        """Initialize ZIP converter."""
        self._markdowner = markdowner
        self._limits = limits or DEFAULT_LIMITS
        self._current_depth = 0

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is a ZIP file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if mimetype in ("application/zip", "application/x-zip-compressed"):
            return True

        if extension == ".zip":
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
        """Convert ZIP to Markdown with recursive conversion."""
        try:
            stream.seek(0)
            with zipfile.ZipFile(stream, "r") as zf:
                entries = sorted(zf.infolist(), key=lambda info: info.filename)
                entry_count = len(entries)
                if not self._limits.check_zip_entry_count(entry_count):
                    raise ZipLimitExceededException(
                        "entries",
                        entry_count,
                        self._limits.max_zip_entries,
                    )

                total_size = sum(info.file_size for info in entries)
                if not self._limits.check_zip_total_size(total_size):
                    raise ZipLimitExceededException(
                        "total_size",
                        total_size,
                        self._limits.max_zip_total_uncompressed_bytes,
                    )

                warnings = []
                results = []
                metadata = {
                    "files_processed": 0,
                    "processed_entries": [],
                    "skipped_entries": [],
                    "failed_entries": [],
                }
                current_depth = kwargs.get("_zip_depth", 0)

                for info in entries:
                    name = info.filename

                    if info.is_dir():
                        continue

                    if not self._limits.check_zip_entry_size(info.file_size):
                        warning = f"Skipped entry too large: {name}"
                        warnings.append(warning)
                        metadata["skipped_entries"].append(
                            {"name": name, "reason": "entry_too_large"}
                        )
                        continue

                    try:
                        content = zf.read(name)
                    except Exception as exc:
                        warning = f"Failed to read ZIP entry {name}: {exc}"
                        warnings.append(warning)
                        metadata["failed_entries"].append(
                            {"name": name, "reason": "read_error"}
                        )
                        continue

                    _, ext = os.path.splitext(name)
                    sub_stream_info = StreamInfo(
                        filename=name,
                        extension=ext.lower() or None,
                    )

                    if ext.lower() == ".zip":
                        next_depth = current_depth + 1
                        if not self._limits.check_recursion_depth(next_depth):
                            warning = f"Skipped nested archive at recursion limit: {name}"
                            warnings.append(warning)
                            metadata["skipped_entries"].append(
                                {"name": name, "reason": "recursion_limit"}
                            )
                            continue
                    else:
                        next_depth = current_depth

                    if self._markdowner is None:
                        results.append(f"## {name}\n\n- Size: {info.file_size} bytes\n")
                        metadata["processed_entries"].append(name)
                        continue

                    try:
                        result = self._markdowner.convert_stream(
                            io.BytesIO(content),
                            stream_info=sub_stream_info,
                            _zip_depth=next_depth,
                        )
                    except UnsupportedFormatException:
                        warning = f"Skipped unsupported ZIP entry: {name}"
                        warnings.append(warning)
                        metadata["skipped_entries"].append(
                            {"name": name, "reason": "unsupported"}
                        )
                        continue
                    except FileConversionException as exc:
                        warning = f"Failed to convert ZIP entry {name}: {exc}"
                        warnings.append(warning)
                        metadata["failed_entries"].append(
                            {"name": name, "reason": "conversion_failed"}
                        )
                        continue
                    except Exception as exc:
                        warning = f"Failed to convert ZIP entry {name}: {exc}"
                        warnings.append(warning)
                        metadata["failed_entries"].append(
                            {"name": name, "reason": "conversion_failed"}
                        )
                        continue

                    entry_lines = [f"## {name}", "", result.text_content]
                    if result.warnings:
                        entry_lines.extend(["", "Warnings:"])
                        entry_lines.extend(f"- {warning}" for warning in result.warnings)
                    results.append("\n".join(entry_lines).strip())
                    metadata["processed_entries"].append(name)
                    metadata["files_processed"] += 1
        except zipfile.BadZipFile as e:
            raise ValueError(f"Bad ZIP file: {e}") from e

        # Build output
        lines = ["# ZIP Archive Contents\n"]

        if results:
            lines.append("\n".join(results))
        else:
            lines.append("\n*No convertible files found*")

        if warnings:
            lines.append("\n## Warnings\n")
            for w in warnings:
                lines.append(f"- {w}")

        return DocumentConverterResult(
            text_content="\n".join(lines),
            metadata=metadata,
            warnings=warnings,
        )
