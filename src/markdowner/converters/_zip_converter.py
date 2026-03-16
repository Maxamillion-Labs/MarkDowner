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

        return self._is_zip_payload(stream)

    @staticmethod
    def _is_zip_payload(stream: BinaryIO) -> bool:
        current_pos = stream.tell()
        try:
            stream.seek(0)
            magic = stream.read(4)
            if magic[:2] != b"PK":
                return False
            stream.seek(0)
            return zipfile.is_zipfile(stream)
        except Exception:
            return False
        finally:
            stream.seek(current_pos)

    @staticmethod
    def _prefix_entry_name(parent_name: str, child_name: str) -> str:
        return f"{parent_name}!{child_name}"

    def _read_entry_bytes(
        self,
        zf: zipfile.ZipFile,
        info: zipfile.ZipInfo,
        total_uncompressed_bytes: int,
        *,
        chunk_size: int = 8192,
    ) -> tuple[bytes, int, int]:
        """Read a ZIP entry incrementally and enforce limits on actual bytes."""
        entry_size = 0
        chunks: list[bytes] = []

        with zf.open(info, "r") as entry_stream:
            while True:
                chunk = entry_stream.read(chunk_size)
                if not chunk:
                    break

                entry_size += len(chunk)
                total_uncompressed_bytes += len(chunk)

                if not self._limits.check_zip_entry_size(entry_size):
                    raise ZipLimitExceededException(
                        "entry_size",
                        entry_size,
                        self._limits.max_zip_entry_bytes,
                    )

                if not self._limits.check_zip_total_size(total_uncompressed_bytes):
                    raise ZipLimitExceededException(
                        "total_size",
                        total_uncompressed_bytes,
                        self._limits.max_zip_total_uncompressed_bytes,
                    )

                chunks.append(chunk)

        return b"".join(chunks), entry_size, total_uncompressed_bytes

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

                warnings = []
                results = []
                metadata = {
                    "entry_names": [info.filename for info in entries if not info.is_dir()],
                    "entry_count": entry_count,
                    "total_uncompressed_bytes": 0,
                    "files_processed": 0,
                    "processed_entries": [],
                    "skipped_entries": [],
                    "failed_entries": [],
                }
                current_depth = kwargs.get("_zip_depth", 0)
                total_uncompressed_bytes = 0

                for info in entries:
                    name = info.filename

                    if info.is_dir():
                        continue

                    try:
                        content, actual_entry_size, total_uncompressed_bytes = self._read_entry_bytes(
                            zf,
                            info,
                            total_uncompressed_bytes,
                        )
                    except Exception as exc:
                        if isinstance(exc, ZipLimitExceededException):
                            raise
                        warning = f"Failed to read ZIP entry {name}: {exc}"
                        warnings.append(warning)
                        metadata["failed_entries"].append(
                            {"name": name, "reason": "read_error", "error": str(exc)}
                        )
                        continue

                    metadata["total_uncompressed_bytes"] = total_uncompressed_bytes

                    _, ext = os.path.splitext(name)
                    sub_stream_info = StreamInfo(
                        filename=name,
                        extension=ext.lower() or None,
                        mimetype=(
                            "application/zip"
                            if ext.lower() == ".zip"
                            else None
                        ),
                    )

                    next_depth = current_depth + 1
                    if not self._limits.check_recursion_depth(next_depth):
                        warning = f"Skipped nested archive at recursion limit: {name}"
                        warnings.append(warning)
                        metadata["skipped_entries"].append(
                            {
                                "name": name,
                                "reason": "recursion_limit",
                                "depth": next_depth,
                            }
                        )
                        continue

                    if self._markdowner is None:
                        results.append(f"## {name}\n\n- Size: {actual_entry_size} bytes\n")
                        metadata["processed_entries"].append(name)
                        continue

                    try:
                        result = self._markdowner.convert_stream(
                            io.BytesIO(content),
                            stream_info=sub_stream_info,
                            _zip_depth=next_depth,
                        )
                    except ZipLimitExceededException:
                        raise
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
                            {
                                "name": name,
                                "reason": "conversion_failed",
                                "error": str(exc),
                            }
                        )
                        continue
                    except Exception as exc:
                        warning = f"Failed to convert ZIP entry {name}: {exc}"
                        warnings.append(warning)
                        metadata["failed_entries"].append(
                            {
                                "name": name,
                                "reason": "conversion_failed",
                                "error": str(exc),
                            }
                        )
                        continue

                    entry_lines = [f"## {name}", "", result.text_content]
                    if result.warnings:
                        warnings.extend(
                            f"{name}: {warning}" for warning in result.warnings
                        )
                        entry_lines.extend(["", "Warnings:"])
                        entry_lines.extend(f"- {warning}" for warning in result.warnings)

                    for child_entry in result.metadata.get("processed_entries", []):
                        metadata["processed_entries"].append(
                            self._prefix_entry_name(name, child_entry)
                        )
                    for child_entry in result.metadata.get("skipped_entries", []):
                        child_copy = dict(child_entry)
                        child_copy["name"] = self._prefix_entry_name(
                            name,
                            child_entry["name"],
                        )
                        metadata["skipped_entries"].append(child_copy)
                    for child_entry in result.metadata.get("failed_entries", []):
                        child_copy = dict(child_entry)
                        child_copy["name"] = self._prefix_entry_name(
                            name,
                            child_entry["name"],
                        )
                        metadata["failed_entries"].append(child_copy)

                    results.append("\n".join(entry_lines).strip())
                    metadata["processed_entries"].append(name)
                    metadata["files_processed"] += 1
        except zipfile.BadZipFile as e:
            return DocumentConverterResult(
                text_content="",
                metadata={"error": f"Bad ZIP file: {e}", "recoverable": True},
                warnings=[f"ZIP parse fallback: {e}"],
            )

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
