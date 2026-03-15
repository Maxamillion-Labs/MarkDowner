# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Fixture corpus smoke tests."""

from pathlib import Path

from markdowner import MarkDowner
from markdowner._stream_info import StreamInfo
from markdowner.converters._docx_converter import DocxConverter
from markdowner.converters._pdf_converter import PdfConverter
from markdowner.converters._xlsx_converter import XlsxConverter


FIXTURES = Path(__file__).parent / "test_files"


def test_fixture_directory_is_populated():
    names = sorted(path.name for path in FIXTURES.iterdir())
    assert names == [
        "sample.csv",
        "sample.docx",
        "sample.html",
        "sample.pdf",
        "sample.rtf",
        "sample.txt",
        "sample.xlsx",
        "sample.zip",
    ]


def test_text_html_csv_and_zip_fixtures_convert():
    md = MarkDowner()

    text_result = md.convert(FIXTURES / "sample.txt")
    html_result = md.convert(FIXTURES / "sample.html")
    csv_result = md.convert(FIXTURES / "sample.csv")
    zip_result = md.convert(FIXTURES / "sample.zip")

    assert "Fixture text line." in text_result.text_content
    assert "# Fixture Title" in html_result.text_content
    assert "Alice" in csv_result.text_content
    assert "zip fixture text" in zip_result.text_content


def test_docx_xlsx_and_pdf_fixtures_match_signature_checks():
    with open(FIXTURES / "sample.docx", "rb") as fh:
        assert DocxConverter().accepts(fh, StreamInfo(extension=".docx"))

    with open(FIXTURES / "sample.xlsx", "rb") as fh:
        assert XlsxConverter().accepts(
            fh,
            StreamInfo(
                extension=".xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )

    with open(FIXTURES / "sample.pdf", "rb") as fh:
        assert PdfConverter().accepts(fh, StreamInfo(extension=".pdf"))
