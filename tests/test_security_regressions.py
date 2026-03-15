# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Adversarial regression coverage for security remediations."""

import io
import os
import stat
import time
import zipfile
from unittest import mock

import pytest

from markdowner import MarkDowner
from markdowner._exceptions import (
    InputSizeExceededException,
    UnsafeLocalSourceException,
    ZipLimitExceededException,
)
from markdowner._limits import Limits
from markdowner._sandbox import (
    ParserSandboxLimits,
    ParserSandboxTimeout,
    ParserSandboxWorkerError,
    run_in_subprocess,
)
from markdowner._stream_info import StreamInfo
from markdowner._temp_utils import materialize_stream_to_temp_path


def _sleep_then_return() -> str:
    time.sleep(2)
    return "done"


def _raise_in_worker() -> None:
    raise RuntimeError("boom")


def test_forged_zip_metadata_vs_real_decompressed_bytes(monkeypatch):
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
        md.convert(io.BytesIO(b"PK"), stream_info=StreamInfo(extension=".zip"))


def test_local_special_file_infinite_stream_path(tmp_path, monkeypatch):
    sample_path = tmp_path / "device.bin"
    sample_path.write_bytes(b"x")
    real_stat = os.stat
    stat_result = real_stat(sample_path)

    def fake_stat(path, *args, **kwargs):
        if str(path) == str(sample_path):
            return os.stat_result(
                (
                    stat.S_IFIFO,
                    stat_result.st_ino,
                    stat_result.st_dev,
                    stat_result.st_nlink,
                    stat_result.st_uid,
                    stat_result.st_gid,
                    stat_result.st_size,
                    stat_result.st_atime,
                    stat_result.st_mtime,
                    stat_result.st_ctime,
                )
            )
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr("markdowner._core.os.stat", fake_stat)

    with pytest.raises(UnsafeLocalSourceException):
        MarkDowner().convert_local(sample_path)


def test_toctou_like_growth_behavior(tmp_path):
    target = tmp_path / "growth.txt"
    target.write_bytes(b"abc")
    md = MarkDowner(limits=Limits(max_input_bytes=10, enabled=True))
    real_open = open

    class GrowingFile:
        def __init__(self, path, mode):
            self._fh = real_open(path, "r+b")
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

    with mock.patch("markdowner._core.open", side_effect=lambda path, mode: GrowingFile(path, mode)):
        with pytest.raises(InputSizeExceededException):
            md.convert_local(target)


def test_parser_timeout_returns_controlled_failure():
    with pytest.raises(ParserSandboxTimeout):
        run_in_subprocess(
            _sleep_then_return,
            limits=ParserSandboxLimits(timeout_seconds=1, memory_limit_bytes=None),
        )


def test_parser_worker_failure_does_not_crash_main_process():
    with pytest.raises(ParserSandboxWorkerError, match="boom"):
        run_in_subprocess(
            _raise_in_worker,
            limits=ParserSandboxLimits(timeout_seconds=5, memory_limit_bytes=None),
        )


def test_temp_paths_scoped_and_cleaned_on_normal_exit():
    temp_path = None
    with materialize_stream_to_temp_path(io.BytesIO(b"hello"), ".txt") as path:
        temp_path = path
        assert path.exists()
        assert oct(path.stat().st_mode & 0o777) == "0o600"
        assert oct(path.parent.stat().st_mode & 0o777) == "0o700"

    assert temp_path is not None
    assert not temp_path.exists()
    assert not temp_path.parent.exists()


def test_nested_archive_complexity_stress_within_limits():
    deepest = io.BytesIO()
    with zipfile.ZipFile(deepest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("deep.txt", "safe nested payload")

    middle = io.BytesIO()
    with zipfile.ZipFile(middle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("deep.zip", deepest.getvalue())

    outer = io.BytesIO()
    with zipfile.ZipFile(outer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("middle.zip", middle.getvalue())

    md = MarkDowner(
        limits=Limits(
            max_recursion_depth=3,
            max_zip_entry_bytes=1024,
            max_zip_total_uncompressed_bytes=4096,
            enabled=True,
        )
    )

    result = md.convert(io.BytesIO(outer.getvalue()), stream_info=StreamInfo(extension=".zip"))

    assert "safe nested payload" in result.text_content
    assert "middle.zip!deep.zip!deep.txt" in result.metadata["processed_entries"]
