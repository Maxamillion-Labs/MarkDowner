# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Audio converter."""

from typing import BinaryIO

from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo


class AudioConverter(DocumentConverter):
    """Converter for audio files."""

    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """Check if this is an audio file."""
        mimetype = stream_info.mimetype or ""
        extension = (stream_info.extension or "").lower()

        if mimetype.startswith("audio/"):
            return True

        audio_extensions = (".mp3", ".wav", ".m4a", ".mp4", ".ogg", ".flac", ".aac", ".wma")
        if extension in audio_extensions:
            return True

        return False

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """Convert audio to Markdown with metadata."""
        # For now, just provide basic info - transcription would require additional deps
        lines = []
        lines.append(f"## Audio: {stream_info.filename or 'unknown'}\n")
        lines.append(f"- **Format**: {stream_info.mimetype or 'unknown'}")
        lines.append(f"- **Extension**: {stream_info.extension or 'unknown'}")

        lines.append("\n*Note: Audio transcription not enabled by default. "
                    "Install additional dependencies for transcription support.*")

        return DocumentConverterResult(text_content="\n".join(lines))