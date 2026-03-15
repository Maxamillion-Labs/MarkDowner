# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""EPUB converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException


class EpubConverter(DocumentConverter):
    """Converter for EPUB files."""

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

        if extension == ".epub":
            return True

        # Check ZIP magic (epub is a zip)
        stream.seek(0)
        magic = stream.read(2)
        stream.seek(0)

        return magic == b"PK"

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert EPUB to Markdown."""
        try:
            from ebook_lib import EBook
        except ImportError:
            raise MissingDependencyException(
                "ebook-lib is required for EPUB conversion. Install with: pip install markdowner[epub]"
            )

        # Save to temp file
        import tempfile
        import os

        stream.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            tmp.write(stream.read())
            tmp_path = tmp.name

        try:
            book = EBook(tmp_path)

            lines = []
            lines.append(f"# {book.title or 'Untitled'}\n")

            if book.author:
                lines.append(f"**Author**: {book.author}\n")

            lines.append("\n## Content\n")

            # Extract text from chapters
            if hasattr(book, 'spine') and book.spine:
                for item in book.spine:
                    if hasattr(book, 'get_item') and callable(book.get_item):
                        try:
                            item_obj = book.get_item(item[0])
                            if item_obj and hasattr(item_obj, 'get_content'):
                                content = item_obj.get_content()
                                if isinstance(content, bytes):
                                    content = content.decode('utf-8', errors='ignore')
                                lines.append(content)
                                lines.append("\n\n")
                        except Exception:
                            pass

            text = "\n".join(lines)
        except Exception as e:
            return DocumentConverterResult(
                text_content="",
                metadata={"error": str(e)},
                warnings=[f"EPUB conversion failed: {e}"],
            )
        finally:
            os.unlink(tmp_path)

        return DocumentConverterResult(text_content=text)