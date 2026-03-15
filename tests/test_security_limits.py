# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test security limits - verify input size and zip limits work correctly."""

import io
import pytest
import tempfile
import os
import zipfile

from markdowner import MarkDowner
from markdowner._limits import Limits, create_custom_limits
from markdowner._exceptions import (
    InputSizeExceededException,
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
