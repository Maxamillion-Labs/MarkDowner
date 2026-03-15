# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""ZIP format routing behavior tests."""

import io
import zipfile

from markdowner._stream_info import StreamInfo
from markdowner.converters._docx_converter import DocxConverter
from markdowner.converters._epub_converter import EpubConverter
from markdowner.converters._pptx_converter import PptxConverter
from markdowner.converters._xlsx_converter import XlsxConverter


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
