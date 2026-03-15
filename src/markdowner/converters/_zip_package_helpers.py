# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Helpers for identifying ZIP-based package formats."""

from __future__ import annotations

import zipfile
from typing import BinaryIO


def zip_has_members(stream: BinaryIO, *required_members: str) -> bool:
    """Return True when the ZIP stream contains every required member."""
    current_pos = stream.tell()
    try:
        stream.seek(0)
        with zipfile.ZipFile(stream, "r") as zf:
            names = set(zf.namelist())
        return all(member in names for member in required_members)
    except zipfile.BadZipFile:
        return False
    finally:
        stream.seek(current_pos)
