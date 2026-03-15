# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Image converter."""

import json
import os
import subprocess
import tempfile
from typing import BinaryIO, Optional

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo


_MINIMUM_EXIFTOOL_VERSION = (12, 24)
_EXIFTOOL_SUCCESS_CACHE: dict[str, tuple[int, ...]] = {}


class ImageConverter(DocumentConverter):
    """Converter for image files."""

    @staticmethod
    def _parse_version(version_text: str) -> tuple[int, ...]:
        parts = version_text.strip().split(".")
        if not parts or any(not part.isdigit() for part in parts):
            raise ValueError(f"Invalid ExifTool version: {version_text!r}")
        return tuple(int(part) for part in parts)

    @classmethod
    def _ensure_safe_exiftool(cls, exiftool_path: str) -> tuple[int, ...]:
        cached_version = _EXIFTOOL_SUCCESS_CACHE.get(exiftool_path)
        if cached_version is not None:
            return cached_version

        version_result = subprocess.run(
            [exiftool_path, "-ver"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if version_result.returncode != 0:
            raise RuntimeError("ExifTool version check failed")

        version = cls._parse_version(version_result.stdout)
        if version < _MINIMUM_EXIFTOOL_VERSION:
            raise RuntimeError(
                f"ExifTool {version_result.stdout.strip()} is below the minimum supported 12.24"
            )

        _EXIFTOOL_SUCCESS_CACHE[exiftool_path] = version
        return version

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is an image file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if mimetype.startswith("image/"):
            return True

        image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg")
        if extension in image_extensions:
            return True

        # Check magic bytes for common image formats
        stream.seek(0)
        magic = stream.read(12)
        stream.seek(0)

        # JPEG
        if magic[:2] == b"\xff\xd8":
            return True
        # PNG
        if magic[:8] == b"\x89PNG\r\n\x1a\n":
            return True
        # GIF
        if magic[:6] in (b"GIF87a", b"GIF89a"):
            return True
        # BMP
        if magic[:2] == b"BM":
            return True

        return False

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert image to Markdown with metadata."""
        warnings = []
        metadata = {}

        # Try to extract EXIF data
        exiftool_path = kwargs.get("exiftool_path")

        if exiftool_path:
            try:
                self._ensure_safe_exiftool(exiftool_path)
            except FileNotFoundError:
                warnings.append("EXIF metadata skipped: ExifTool executable not found")
            except ValueError as exc:
                warnings.append(f"EXIF metadata skipped: {exc}")
            except RuntimeError as exc:
                warnings.append(f"EXIF metadata skipped: {exc}")
            else:
                # Save to temp file

                stream.seek(0)
                ext = stream_info.extension or ".jpg"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(stream.read())
                    tmp_path = tmp.name

                try:
                    result = subprocess.run(
                        [exiftool_path, "-j", tmp_path],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False,
                    )

                    if result.returncode == 0 and result.stdout:
                        exif_data = json.loads(result.stdout)
                        if exif_data:
                            metadata["exif"] = exif_data[0] if exif_data else {}
                    else:
                        warnings.append("EXIF metadata skipped: ExifTool returned no metadata")
                except Exception as exc:
                    warnings.append(f"EXIF metadata skipped: metadata extraction failed ({exc})")
                finally:
                    os.unlink(tmp_path)
        else:
            warnings.append("EXIF metadata skipped: ExifTool not configured")

        # Build markdown
        lines = []
        lines.append(f"## Image: {stream_info.filename or 'unknown'}\n")

        if metadata.get("exif"):
            exif = metadata["exif"]
            lines.append("### Metadata\n")
            for key in ["ImageWidth", "ImageHeight", "Make", "Model", "DateTimeOriginal"]:
                if key in exif:
                    lines.append(f"- **{key}**: {exif[key]}")

        if not metadata.get("exif"):
            lines.append("\n*No metadata available*")
            if not warnings:
                warnings.append("No EXIF metadata found")

        return DocumentConverterResult(
            text_content="\n".join(lines),
            metadata=metadata,
            warnings=warnings,
        )
