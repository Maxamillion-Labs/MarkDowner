# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Helpers for identifying ZIP-based package formats."""

from __future__ import annotations

import zipfile
from typing import BinaryIO


def zip_has_members(
    stream: BinaryIO,
    *required_members: str,
    max_entries: int,
    max_metadata_bytes: int,
) -> bool:
    """Return True when the ZIP stream contains every required member."""
    current_pos = stream.tell()
    try:
        stream.seek(0)
        with zipfile.ZipFile(stream, "r") as zf:
            remaining = set(required_members)
            metadata_bytes = 0

            for index, info in enumerate(zf.infolist(), start=1):
                if index > max_entries:
                    return False

                metadata_bytes += len(info.filename.encode("utf-8", errors="ignore"))
                metadata_bytes += len(info.comment)
                if metadata_bytes > max_metadata_bytes:
                    return False

                remaining.discard(info.filename)
                if not remaining:
                    return True

        return False
    except zipfile.BadZipFile:
        return False
    finally:
        stream.seek(current_pos)
