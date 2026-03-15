# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""EPUB converter."""

from typing import BinaryIO

from bs4 import BeautifulSoup
from markdownify import markdownify as to_markdown

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._limits import DEFAULT_LIMITS, Limits
from .._sandbox import ParserSandboxLimits, run_in_subprocess
from .._stream_info import StreamInfo
from .._temp_utils import materialize_stream_to_temp_path
from .._exceptions import MissingDependencyException
from ._zip_package_helpers import zip_has_members


def _convert_epub_to_payload(epub_path: str) -> tuple[str, list[str]]:
    from ebooklib import ITEM_DOCUMENT, epub

    book = epub.read_epub(epub_path)
    warnings = []

    lines = []
    title = ""
    authors = []
    try:
        title_meta = book.get_metadata("DC", "title")
        if title_meta:
            title = title_meta[0][0]
        author_meta = book.get_metadata("DC", "creator")
        authors = [item[0] for item in author_meta]
    except Exception as exc:
        warnings.append(f"EPUB metadata unavailable: {exc}")

    lines.append(f"# {title or 'Untitled'}\n")

    if authors:
        lines.append(f"**Author**: {', '.join(authors)}\n")

    lines.append("\n## Content\n")

    for item in book.get_items():
        if item.get_type() != ITEM_DOCUMENT:
            continue
        try:
            content = item.get_content().decode("utf-8", errors="replace")
            soup = BeautifulSoup(content, "html.parser")
            for element in soup(["script", "style"]):
                element.decompose()
            chapter_text = to_markdown(str(soup), heading_style="ATX").strip()
            if chapter_text:
                lines.append(chapter_text)
                lines.append("\n")
        except Exception as exc:
            warnings.append(f"EPUB content skipped: {exc}")

    return "\n".join(lines), warnings


class EpubConverter(DocumentConverter):
    """Converter for EPUB files."""

    def __init__(self, limits: Limits = DEFAULT_LIMITS):
        self._limits = limits

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is an EPUB file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if mimetype == "application/epub+zip":
            return True

        if extension != ".epub" and mimetype:
            return False

        return zip_has_members(
            stream,
            "mimetype",
            "META-INF/container.xml",
            max_entries=self._limits.max_zip_metadata_entries,
            max_metadata_bytes=self._limits.max_zip_metadata_scan_bytes,
        )

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert EPUB to Markdown."""
        try:
            from ebooklib import ITEM_DOCUMENT, epub
        except ImportError:
            raise MissingDependencyException(
                "ebooklib is required for EPUB conversion. Install with: pip install markdowner[epub]"
            )

        del epub

        try:
            with materialize_stream_to_temp_path(stream, ".epub") as tmp_path:
                text, warnings = run_in_subprocess(
                    _convert_epub_to_payload,
                    str(tmp_path),
                    limits=ParserSandboxLimits(),
                )
        except Exception as e:
            raise RuntimeError(f"EPUB conversion failed: {e}") from e

        return DocumentConverterResult(text_content=text, warnings=warnings)
