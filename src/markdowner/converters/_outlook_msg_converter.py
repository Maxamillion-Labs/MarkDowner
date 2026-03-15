# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Outlook MSG converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._sandbox import ParserSandboxLimits, run_in_subprocess
from .._stream_info import StreamInfo
from .._temp_utils import materialize_stream_to_temp_path
from .._exceptions import MissingDependencyException


def _convert_msg_to_payload(msg_path: str) -> tuple[str, list[str]]:
    import olefile

    ole = olefile.OleFileIO(msg_path)
    try:
        lines = []
        warnings = []

        if ole.exists("__substg1.0_0037001F"):
            subject = ole.openstream("__substg1.0_0037001F").read()
            try:
                lines.append(f"# {subject.decode('utf-16-le').rstrip(chr(0))}\n")
            except Exception as exc:
                warnings.append(f"MSG subject skipped: {exc}")

        if ole.exists("__substg1.0_0C1F001F"):
            sender = ole.openstream("__substg1.0_0C1F001F").read()
            try:
                lines.append(f"**From**: {sender.decode('utf-16-le').rstrip(chr(0))}\n")
            except Exception as exc:
                warnings.append(f"MSG sender skipped: {exc}")

        if ole.exists("__substg1.0_1000001F"):
            body = ole.openstream("__substg1.0_1000001F").read()
            try:
                lines.append(body.decode("utf-16-le").rstrip("\x00"))
            except Exception as exc:
                warnings.append(f"MSG body skipped: {exc}")

        return "\n".join(lines), warnings
    finally:
        ole.close()


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

        del olefile

        try:
            with materialize_stream_to_temp_path(stream, ".msg") as tmp_path:
                text, warnings = run_in_subprocess(
                    _convert_msg_to_payload,
                    str(tmp_path),
                    limits=ParserSandboxLimits(),
                )
        except Exception as e:
            raise RuntimeError(f"MSG conversion failed: {e}") from e

        return DocumentConverterResult(text_content=text, warnings=warnings)
