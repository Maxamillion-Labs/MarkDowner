# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test security limits - verify input size and zip limits work correctly."""

import io
import os
import stat
import tempfile
import zipfile
from unittest import mock

import pytest

from markdowner import MarkDowner
from markdowner._limits import Limits, create_custom_limits
from markdowner._exceptions import (
    InputSizeExceededException,
    UnsafeLocalSourceException,
    ZipLimitExceededException,
)
from markdowner._stream_info import StreamInfo


class TestInputSizeLimits:
    """Test input size limits."""

    def test_default_limit_allows_normal_input(self):
        """Normal input should be allowed."""
        limits = Limits(max_input_bytes=1000, enabled=True)
        assert limits.check_input_size(500) is True

    def test_default_limit_blocks_oversized_input(self):
        """Oversized input should be blocked."""
        limits = Limits(max_input_bytes=1000, enabled=True)
        assert limits.check_input_size(2000) is False

    def test_limits_disabled_allows_any_size(self):
        """When disabled, limits should not block."""
        limits = Limits(max_input_bytes=1000, enabled=False)
        assert limits.check_input_size(1000000) is True

    def test_input_size_exception_raised(self):
        """InputSizeExceededException should be raised for large input."""
        limits = Limits(max_input_bytes=10, enabled=True)
        md = MarkDowner(limits=limits)

        # Create content larger than limit
        content = b"x" * 100

        with pytest.raises(InputSizeExceededException) as exc_info:
            md.convert(io.BytesIO(content))

        assert "100" in str(exc_info.value)
        assert "10" in str(exc_info.value)

    def test_input_size_exception_for_unseekable_stream(self):
        """Oversized unseekable streams should fail before full buffering."""
        limits = Limits(max_input_bytes=10, enabled=True)
        md = MarkDowner(limits=limits)

        class UnseekableStream:
            def __init__(self, payload: bytes):
                self._buffer = io.BytesIO(payload)
                self.bytes_read = 0

            def read(self, size: int = -1) -> bytes:
                chunk = self._buffer.read(size)
                self.bytes_read += len(chunk)
                return chunk

            def seekable(self) -> bool:
                return False

        stream = UnseekableStream(b"x" * 32)
        with pytest.raises(InputSizeExceededException):
            md.convert_stream(stream)

        assert stream.bytes_read == 11

    def test_local_special_file_is_blocked_or_bounded(self, tmp_path, monkeypatch):
        """Non-regular local sources should be rejected explicitly."""
        sample_path = tmp_path / "special.bin"
        sample_path.write_bytes(b"ignored")
        real_fstat = os.fstat

        def fake_fstat(fd):
            real_stat = real_fstat(fd)
            return os.stat_result(
                (
                    stat.S_IFCHR,
                    real_stat.st_ino,
                    real_stat.st_dev,
                    real_stat.st_nlink,
                    real_stat.st_uid,
                    real_stat.st_gid,
                    real_stat.st_size,
                    real_stat.st_atime,
                    real_stat.st_mtime,
                    real_stat.st_ctime,
                )
            )

        monkeypatch.setattr("markdowner._core.os.fstat", fake_fstat)

        with pytest.raises(UnsafeLocalSourceException):
            MarkDowner().convert_local(sample_path)

    def test_local_file_growth_toctou_still_stops_at_limit(self, tmp_path):
        """Read-time bounds should still stop a file that grows after stat."""
        target = tmp_path / "growth.txt"
        target.write_bytes(b"abc")

        limits = Limits(max_input_bytes=10, enabled=True)
        md = MarkDowner(limits=limits)

        real_open = open

        class GrowingFile:
            def __init__(self, fd, mode, closefd=True):
                self._fh = real_open(target, "r+b")
                self._expanded = False

            def __getattr__(self, name):
                return getattr(self._fh, name)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return self._fh.__exit__(exc_type, exc, tb)

            def read(self, size=-1):
                if not self._expanded:
                    self._fh.seek(0, os.SEEK_END)
                    self._fh.write(b"x" * 32)
                    self._fh.flush()
                    self._fh.seek(0)
                    self._expanded = True
                return self._fh.read(size)

        with mock.patch("markdowner._core.os.fdopen", side_effect=lambda fd, mode, closefd=True: GrowingFile(fd, mode, closefd)):
            with pytest.raises(InputSizeExceededException):
                md.convert_local(target)


class TestZipLimits:
    """Test ZIP archive limits."""

    def test_zip_entry_count_limit(self):
        """Too many entries should be blocked."""
        limits = Limits(max_zip_entries=10, enabled=True)
        assert limits.check_zip_entry_count(5) is True
        assert limits.check_zip_entry_count(15) is False

    def test_zip_total_size_limit(self):
        """Total uncompressed size limit should work."""
        limits = Limits(max_zip_total_uncompressed_bytes=1000, enabled=True)
        assert limits.check_zip_total_size(500) is True
        assert limits.check_zip_total_size(2000) is False

    def test_zip_entry_size_limit(self):
        """Individual entry size limit should work."""
        limits = Limits(max_zip_entry_bytes=1000, enabled=True)
        assert limits.check_zip_entry_size(500) is True
        assert limits.check_zip_entry_size(2000) is False

    def test_zip_too_many_entries_raises_exception(self):
        """Too many entries should fail with ZIP limit error."""
        # Create a zip with too many entries
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zf:
                for i in range(100):
                    zf.writestr(f"file{i}.txt", "content")
            tmp_path = tmp.name

        try:
            limits = Limits(max_zip_entries=10, enabled=True)
            md = MarkDowner(limits=limits)

            # The limit should be mentioned in the error
            with pytest.raises(Exception) as exc_info:
                md.convert(tmp_path)
            
            # Check that ZIP limit is mentioned in the error
            error_msg = str(exc_info.value)
            assert "10" in error_msg or "entries" in error_msg.lower()
        finally:
            os.unlink(tmp_path)

    def test_zip_streaming_enforces_entry_limit_on_actual_bytes(self, monkeypatch):
        """Forged ZIP metadata should not bypass the actual entry-size limit."""
        limits = Limits(max_zip_entry_bytes=8, enabled=True)
        md = MarkDowner(limits=limits)

        class FakeEntryStream:
            def __init__(self, chunks):
                self._chunks = list(chunks)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self, size=-1):
                if not self._chunks:
                    return b""
                return self._chunks.pop(0)

        class FakeZipFile:
            def __init__(self, stream, mode):
                self._info = zipfile.ZipInfo("payload.txt")
                self._info.file_size = 1

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def infolist(self):
                return [self._info]

            def open(self, info, mode="r"):
                return FakeEntryStream([b"12345", b"6789"])

        monkeypatch.setattr("markdowner.converters._zip_converter.zipfile.ZipFile", FakeZipFile)

        with pytest.raises(ZipLimitExceededException, match="entry_size"):
            md.convert(
                io.BytesIO(b"PK"),
                stream_info=StreamInfo(extension=".zip"),
            )

    def test_zip_streaming_enforces_total_limit_on_actual_bytes(self, monkeypatch):
        """Actual uncompressed totals should be enforced while streaming."""
        limits = Limits(max_zip_total_uncompressed_bytes=10, enabled=True)
        md = MarkDowner(limits=limits)

        class FakeEntryStream:
            def __init__(self, chunks):
                self._chunks = list(chunks)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self, size=-1):
                if not self._chunks:
                    return b""
                return self._chunks.pop(0)

        class FakeZipFile:
            def __init__(self, stream, mode):
                self._entries = []
                for name in ("a.txt", "b.txt"):
                    info = zipfile.ZipInfo(name)
                    info.file_size = 1
                    self._entries.append(info)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def infolist(self):
                return self._entries

            def open(self, info, mode="r"):
                return FakeEntryStream([b"123456"])

        monkeypatch.setattr("markdowner.converters._zip_converter.zipfile.ZipFile", FakeZipFile)

        with pytest.raises(ZipLimitExceededException, match="total_size"):
            md.convert(
                io.BytesIO(b"PK"),
                stream_info=StreamInfo(extension=".zip"),
            )

    def test_nested_zip_bomb_stops_with_limit_exception(self):
        """Nested archives should stop once streamed bytes cross the limit."""
        inner_archive = io.BytesIO()
        with zipfile.ZipFile(inner_archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("huge.txt", b"x" * 256)

        outer_archive = io.BytesIO()
        with zipfile.ZipFile(outer_archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("nested.zip", inner_archive.getvalue())

        md = MarkDowner(
            limits=Limits(
                max_zip_entry_bytes=128,
                max_zip_total_uncompressed_bytes=512,
                enabled=True,
            )
        )

        with pytest.raises(ZipLimitExceededException):
            md.convert(
                io.BytesIO(outer_archive.getvalue()),
                stream_info=StreamInfo(extension=".zip"),
            )


class TestRecursionLimits:
    """Test recursion depth limits."""

    def test_recursion_depth_limit(self):
        """Recursion depth should be limited."""
        limits = Limits(max_recursion_depth=2, enabled=True)
        assert limits.check_recursion_depth(1) is True
        assert limits.check_recursion_depth(2) is True
        assert limits.check_recursion_depth(3) is False

    def test_nested_zip_recursion_limit(self):
        """Nested ZIP archives beyond the limit should be skipped with a warning."""
        deepest_zip = io.BytesIO()
        with zipfile.ZipFile(deepest_zip, "w") as zf:
            zf.writestr("deep.txt", "deep content")

        inner_zip = io.BytesIO()
        with zipfile.ZipFile(inner_zip, "w") as zf:
            zf.writestr("deeper.zip", deepest_zip.getvalue())

        outer_zip = io.BytesIO()
        with zipfile.ZipFile(outer_zip, "w") as zf:
            zf.writestr("nested.zip", inner_zip.getvalue())

        md = MarkDowner(limits=Limits(max_recursion_depth=1, enabled=True))
        result = md.convert(
            io.BytesIO(outer_zip.getvalue()),
            stream_info=StreamInfo(extension=".zip"),
        )

        assert "nested.zip" in result.metadata["processed_entries"]
        assert any(
            entry["name"] == "nested.zip!deeper.zip"
            and entry["reason"] == "recursion_limit"
            for entry in result.metadata["skipped_entries"]
        )
        assert any("recursion limit" in warning.lower() for warning in result.warnings)


class TestLimitsFactory:
    """Test Limits factory function."""

    def test_create_custom_limits(self):
        """Custom limits should override defaults."""
        limits = create_custom_limits(
            max_input_bytes=5000,
            max_zip_entries=50,
        )

        assert limits.max_input_bytes == 5000
        assert limits.max_zip_entries == 50
        # Other values should be defaults
        assert limits.max_zip_total_uncompressed_bytes == 200 * 1024 * 1024

    def test_create_custom_limits_preserves_zero_values(self):
        """Explicit zero-valued limits should not be replaced by defaults."""
        limits = create_custom_limits(max_recursion_depth=0)

        assert limits.max_recursion_depth == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
