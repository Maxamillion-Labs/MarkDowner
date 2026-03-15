# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Seekable stream wrapper that enforces a maximum readable byte boundary."""

from __future__ import annotations

import io
from typing import BinaryIO

from ._exceptions import InputSizeExceededException


class BoundedStream(io.BufferedIOBase):
    """Wrap a seekable binary stream and reject reads past the configured limit."""

    def __init__(self, stream: BinaryIO, max_bytes: int):
        self._stream = stream
        self._max_bytes = max_bytes

    def __getattr__(self, name: str):
        return getattr(self._stream, name)

    @property
    def closed(self) -> bool:
        return self._stream.closed

    def close(self) -> None:
        self._stream.close()

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def tell(self) -> int:
        return self._stream.tell()

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._stream.seek(offset, whence)

    def read(self, size: int = -1) -> bytes:
        start = self._stream.tell()
        remaining = self._max_bytes - start

        if remaining < 0:
            raise InputSizeExceededException(start, self._max_bytes, "size")

        read_size = size
        if size is None or size < 0:
            read_size = remaining + 1
        elif size > remaining:
            read_size = remaining + 1

        chunk = self._stream.read(read_size)
        end = start + len(chunk)
        if end > self._max_bytes:
            raise InputSizeExceededException(end, self._max_bytes, "size")
        return chunk
