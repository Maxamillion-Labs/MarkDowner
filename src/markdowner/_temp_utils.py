# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Temporary file helpers with scoped directories and restrictive permissions."""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator


@contextmanager
def materialize_stream_to_temp_path(stream: BinaryIO, suffix: str) -> Iterator[Path]:
    """Write a stream to a temp file inside a private temp directory."""
    stream.seek(0)
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chmod(temp_dir, 0o700)
        temp_path = Path(temp_dir) / f"input{suffix}"
        with open(temp_path, "wb") as temp_file:
            temp_file.write(stream.read())
        os.chmod(temp_path, 0o600)
        yield temp_path
