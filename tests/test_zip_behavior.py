# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""ZIP format routing behavior tests."""

import io
import zipfile

from markdowner._limits import Limits
from markdowner._stream_info import StreamInfo
from markdowner.converters._docx_converter import DocxConverter
from markdowner.converters._epub_converter import EpubConverter
from markdowner.converters._pptx_converter import PptxConverter
from markdowner.converters._xlsx_converter import XlsxConverter
from markdowner.converters._zip_package_helpers import zip_has_members


def _plain_zip_bytes() -> bytes:
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("notes.txt", "plain zip content")
    return archive.getvalue()


def test_plain_zip_is_not_misclassified_as_docx():
    assert not DocxConverter().accepts(
        io.BytesIO(_plain_zip_bytes()),
        StreamInfo(extension=".docx"),
    )


def test_plain_zip_is_not_misclassified_as_pptx():
    assert not PptxConverter().accepts(
        io.BytesIO(_plain_zip_bytes()),
        StreamInfo(extension=".pptx"),
    )


def test_plain_zip_is_not_misclassified_as_xlsx():
    assert not XlsxConverter().accepts(
        io.BytesIO(_plain_zip_bytes()),
        StreamInfo(extension=".xlsx"),
    )


def test_plain_zip_is_not_misclassified_as_epub():
    assert not EpubConverter().accepts(
        io.BytesIO(_plain_zip_bytes()),
        StreamInfo(extension=".epub"),
    )


def test_zip_member_scan_has_hard_entry_cap(monkeypatch):
    class FakeInfo:
        def __init__(self, filename):
            self.filename = filename
            self.comment = b""

    class LimitedIterable:
        def __iter__(self):
            for index in range(5):
                if index >= 3:
                    raise AssertionError("scan exceeded expected short-circuit bound")
                yield FakeInfo(f"file-{index}.xml")

    class FakeZipFile:
        def __init__(self, stream, mode):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def infolist(self):
            return LimitedIterable()

    monkeypatch.setattr("markdowner.converters._zip_package_helpers.zipfile.ZipFile", FakeZipFile)

    assert not zip_has_members(
        io.BytesIO(b"PK"),
        "word/document.xml",
        max_entries=2,
        max_metadata_bytes=1024,
    )


def test_acceptors_do_not_scan_unbounded_zip_metadata(monkeypatch):
    seen = []

    def fake_zip_has_members(stream, *required_members, max_entries, max_metadata_bytes):
        seen.append((required_members, max_entries, max_metadata_bytes))
        return False

    monkeypatch.setattr("markdowner.converters._docx_converter.zip_has_members", fake_zip_has_members)
    monkeypatch.setattr("markdowner.converters._pptx_converter.zip_has_members", fake_zip_has_members)
    monkeypatch.setattr("markdowner.converters._xlsx_converter.zip_has_members", fake_zip_has_members)
    monkeypatch.setattr("markdowner.converters._epub_converter.zip_has_members", fake_zip_has_members)

    limits = Limits(max_zip_metadata_entries=7, max_zip_metadata_scan_bytes=123, enabled=True)
    payload = io.BytesIO(_plain_zip_bytes())

    assert not DocxConverter(limits=limits).accepts(io.BytesIO(payload.getvalue()), StreamInfo(extension=".docx"))
    assert not PptxConverter(limits=limits).accepts(io.BytesIO(payload.getvalue()), StreamInfo(extension=".pptx"))
    assert not XlsxConverter(limits=limits).accepts(io.BytesIO(payload.getvalue()), StreamInfo(extension=".xlsx"))
    assert not EpubConverter(limits=limits).accepts(io.BytesIO(payload.getvalue()), StreamInfo(extension=".epub"))

    assert len(seen) == 4
    assert all(entry[1] == 7 for entry in seen)
    assert all(entry[2] == 123 for entry in seen)
