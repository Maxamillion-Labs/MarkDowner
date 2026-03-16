# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Outlook MSG converter."""

import io
import os
from typing import Any, BinaryIO, List

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._sandbox import ParserSandboxLimits, run_in_subprocess
from .._stream_info import StreamInfo
from .._temp_utils import materialize_stream_to_temp_path
from .._exceptions import MissingDependencyException


# Increase timeout for MSG files with attachments (they can be slow to parse)
MSG_PARSER_TIMEOUT_SECONDS = 120
ATTACH_EMBEDDED_MESSAGE = 5
ATTACH_OLE = 6


def _read_utf16_stream(ole: Any, path: list[str]) -> str | None:
    if not ole.exists(path):
        return None
    try:
        return ole.openstream(path).read().decode("utf-16-le").rstrip("\x00")
    except Exception:
        return None


def _read_attachment_method(ole: Any, storage_name: str) -> int | None:
    method_path = [storage_name, "__substg1.0_37050003"]
    if not ole.exists(method_path):
        return None
    try:
        data = ole.openstream(method_path).read()
        if len(data) < 4:
            return None
        return int.from_bytes(data[:4], "little")
    except Exception:
        return None


def _convert_msg_to_payload(msg_path: str) -> tuple[str, List[str], List[dict]]:
    import olefile

    ole = olefile.OleFileIO(msg_path)
    try:
        lines = []
        warnings = []
        attachments = []

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

        attachment_storages = set()
        for entry in ole.listdir():
            if len(entry) >= 1 and entry[0].startswith("__attach_version1.0_"):
                attachment_storages.add(entry[0])
        
        for idx, storage_name in enumerate(sorted(attachment_storages)):
            name = _read_utf16_stream(ole, [storage_name, "__substg1.0_3704001F"])
            if not name:
                name = _read_utf16_stream(ole, [storage_name, "__substg1.0_3703001F"])
            if not name:
                name = f"attachment-{idx + 1}.bin"

            content = None
            try:
                data_path = [storage_name, "__substg1.0_37010102"]
                content = ole.openstream(data_path).read()
            except Exception:
                pass

            if content and len(content) > 0:
                attachments.append({
                    "name": name,
                    "content": content,
                    "method": _read_attachment_method(ole, storage_name),
                })
                continue

            method = _read_attachment_method(ole, storage_name)
            if method in (ATTACH_EMBEDDED_MESSAGE, ATTACH_OLE) or ole.exists(
                [storage_name, "__substg1.0_3701000D"]
            ):
                warnings.append(
                    f"attachment skipped ({name}): unsupported embedded outlook item"
                )
            else:
                warnings.append(f"attachment skipped ({name}): no content")

        return "\n".join(lines), warnings, attachments
    finally:
        ole.close()


class OutlookMsgConverter(DocumentConverter):
    """Converter for Outlook MSG files."""

    def __init__(self, markdowner=None, limits=None):
        """Initialize MSG converter with optional markdowner for attachment conversion."""
        self._markdowner = markdowner
        self._limits = limits

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
                text, warnings, attachments = run_in_subprocess(
                    _convert_msg_to_payload,
                    str(tmp_path),
                    limits=ParserSandboxLimits(timeout_seconds=MSG_PARSER_TIMEOUT_SECONDS),
                )
        except Exception as e:
            raise RuntimeError(f"MSG conversion failed: {e}") from e

        attachment_outputs = []
        if self._markdowner and attachments:
            for att in attachments:
                content = att.get("content")
                if not content:
                    warnings.append(
                        f"attachment skipped ({att.get('name', 'unknown')}): no content"
                    )
                    continue

                name = att.get("name", "attachment.bin")
                _, ext = os.path.splitext(name)
                att_stream_info = StreamInfo(
                    filename=name,
                    extension=ext.lower() if ext else None,
                )

                try:
                    att_result = self._markdowner.convert_stream(
                        io.BytesIO(content),
                        stream_info=att_stream_info,
                    )
                    if att_result.text_content.strip():
                        attachment_outputs.append(
                            {
                                "name": name,
                                "markdown": att_result.text_content,
                            }
                        )
                        warnings.extend(
                            f"{name}: {warning}" for warning in att_result.warnings
                        )
                    else:
                        warnings.append(f"attachment skipped ({name}): no conversion output")
                except Exception as exc:
                    warnings.append(f"attachment skipped ({name}): {exc}")

        metadata = {"attachment_outputs": attachment_outputs}

        return DocumentConverterResult(
            text_content=text,
            warnings=warnings,
            metadata=metadata,
        )
