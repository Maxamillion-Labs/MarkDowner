# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Focused tests for MSG conversion edge cases."""

import io
import sys
import types
from pathlib import Path

import pytest

from markdowner._stream_info import StreamInfo
from markdowner.converters._outlook_msg_converter import (
    OutlookMsgConverter,
    _convert_msg_to_payload,
)


class _FakeMarkdowner:
    def __init__(self, exc: Exception | None = None):
        self.exc = exc
        self.calls = []

    def convert_stream(self, stream, *, stream_info):
        self.calls.append((stream.read(), stream_info.filename))
        if self.exc is not None:
            raise self.exc
        return types.SimpleNamespace(
            text_content="attachment markdown",
            warnings=["inner warning"],
        )


def test_msg_converter_cleans_temp_workspace_on_success(monkeypatch):
    captured_path = None

    def fake_run_in_subprocess(func, path, *, limits):
        nonlocal captured_path
        captured_path = Path(path)
        assert captured_path.exists()
        return ("body", [], [])

    monkeypatch.setattr(
        "markdowner.converters._outlook_msg_converter.run_in_subprocess",
        fake_run_in_subprocess,
    )

    result = OutlookMsgConverter().convert(
        io.BytesIO(b"msg-body"),
        StreamInfo(extension=".msg"),
    )

    assert result.text_content == "body"
    assert captured_path is not None
    assert not captured_path.exists()
    assert not captured_path.parent.exists()


def test_msg_converter_cleans_temp_workspace_on_failure(monkeypatch):
    captured_path = None

    def fake_run_in_subprocess(func, path, *, limits):
        nonlocal captured_path
        captured_path = Path(path)
        assert captured_path.exists()
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "markdowner.converters._outlook_msg_converter.run_in_subprocess",
        fake_run_in_subprocess,
    )

    with pytest.raises(RuntimeError, match="MSG conversion failed: boom"):
        OutlookMsgConverter().convert(
            io.BytesIO(b"msg-body"),
            StreamInfo(extension=".msg"),
        )

    assert captured_path is not None
    assert not captured_path.exists()
    assert not captured_path.parent.exists()


def test_msg_attachment_failure_is_non_fatal(monkeypatch):
    markdowner = _FakeMarkdowner(exc=RuntimeError("attachment decoder failed"))
    converter = OutlookMsgConverter(markdowner=markdowner)

    monkeypatch.setattr(
        "markdowner.converters._outlook_msg_converter.run_in_subprocess",
        lambda func, path, *, limits: (
            "body",
            [],
            [{"name": "note.txt", "content": b"payload"}],
        ),
    )

    result = converter.convert(io.BytesIO(b"msg-body"), StreamInfo(extension=".msg"))

    assert result.text_content == "body"
    assert result.metadata["attachment_outputs"] == []
    assert markdowner.calls == [(b"payload", "note.txt")]
    assert result.warnings == [
        "attachment skipped (note.txt): attachment decoder failed"
    ]


def test_msg_attachment_warnings_are_prefixed(monkeypatch):
    markdowner = _FakeMarkdowner()
    converter = OutlookMsgConverter(markdowner=markdowner)

    monkeypatch.setattr(
        "markdowner.converters._outlook_msg_converter.run_in_subprocess",
        lambda func, path, *, limits: (
            "body",
            [],
            [{"name": "note.txt", "content": b"payload"}],
        ),
    )

    result = converter.convert(io.BytesIO(b"msg-body"), StreamInfo(extension=".msg"))

    assert result.metadata["attachment_outputs"] == [
        {"name": "note.txt", "markdown": "attachment markdown"}
    ]
    assert "note.txt: inner warning" in result.warnings


def test_msg_payload_warns_for_embedded_outlook_item(monkeypatch):
    class FakeStream:
        def __init__(self, data: bytes):
            self._data = data

        def read(self):
            return self._data

    class FakeOle:
        def __init__(self, path):
            self.path = path

        def exists(self, path):
            key = tuple(path) if isinstance(path, list) else path
            return key in {
                "__substg1.0_0037001F",
                ("__attach_version1.0_#00000000", "__substg1.0_3704001F"),
                ("__attach_version1.0_#00000000", "__substg1.0_37050003"),
                ("__attach_version1.0_#00000000", "__substg1.0_3701000D"),
            }

        def openstream(self, path):
            key = tuple(path) if isinstance(path, list) else path
            payloads = {
                "__substg1.0_0037001F": "Subject".encode("utf-16-le"),
                ("__attach_version1.0_#00000000", "__substg1.0_3704001F"): "embedded.msg".encode("utf-16-le"),
                ("__attach_version1.0_#00000000", "__substg1.0_37050003"): (5).to_bytes(4, "little"),
            }
            return FakeStream(payloads[key])

        def listdir(self):
            return [
                ["__attach_version1.0_#00000000", "__substg1.0_3704001F"],
                ["__attach_version1.0_#00000000", "__substg1.0_37050003"],
                ["__attach_version1.0_#00000000", "__substg1.0_3701000D"],
            ]

        def close(self):
            return None

    fake_module = types.SimpleNamespace(OleFileIO=FakeOle)
    monkeypatch.setitem(sys.modules, "olefile", fake_module)

    text, warnings, attachments = _convert_msg_to_payload("ignored.msg")

    assert "Subject" in text
    assert attachments == []
    assert warnings == [
        "attachment skipped (embedded.msg): unsupported embedded outlook item"
    ]
