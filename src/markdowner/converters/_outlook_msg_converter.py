# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Outlook MSG converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException


class OutlookMsgConverter(DocumentConverter):
    """Converter for Outlook MSG files."""

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is an MSG file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if "outlook" in mimetype or "vnd.ms-outlook" in mimetype:
            return True

        if extension == ".msg":
            return True

        # Check OLE magic
        stream.seek(0)
        magic = stream.read(8)
        stream.seek(0)

        return magic[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert MSG to Markdown."""
        try:
            import olefile
        except ImportError:
            raise MissingDependencyException(
                "olefile is required for MSG conversion. Install with: pip install markdowner[outlook]"
            )

        # Save to temp file
        import tempfile
        import os

        stream.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".msg", delete=False) as tmp:
            tmp.write(stream.read())
            tmp_path = tmp.name

        try:
            ole = olefile.OleFileIO(tmp_path)

            lines = []
            warnings = []

            # Try to get subject
            if ole.exists("__substg1.0_0037001F"):
                subject = ole.openstream("__substg1.0_0037001F").read()
                try:
                    subject = subject.decode("utf-16-le").rstrip("\x00")
                    lines.append(f"# {subject}\n")
                except Exception as exc:
                    warnings.append(f"MSG subject skipped: {exc}")

            # Try to get sender
            if ole.exists("__substg1.0_0C1F001F"):
                sender = ole.openstream("__substg1.0_0C1F001F").read()
                try:
                    sender = sender.decode("utf-16-le").rstrip("\x00")
                    lines.append(f"**From**: {sender}\n")
                except Exception as exc:
                    warnings.append(f"MSG sender skipped: {exc}")

            # Get body
            if ole.exists("__substg1.0_1000001F"):
                body = ole.openstream("__substg1.0_1000001F").read()
                try:
                    body = body.decode("utf-16-le").rstrip("\x00")
                    lines.append(body)
                except Exception as exc:
                    warnings.append(f"MSG body skipped: {exc}")

            ole.close()
            text = "\n".join(lines)
        except Exception as e:
            raise RuntimeError(f"MSG conversion failed: {e}") from e
        finally:
            os.unlink(tmp_path)

        return DocumentConverterResult(text_content=text, warnings=warnings)
