# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""
Stream info module for MarkDowner.

Provides the StreamInfo class to track metadata about files being converted.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class StreamInfo:
    """
    Metadata about a stream being converted.

    This class captures information about the source file or stream
    to help converters determine if they can handle the content.
    """

    # MIME type (e.g., "application/pdf")
    mimetype: Optional[str] = None

    # File extension including leading dot (e.g., ".pdf")
    extension: Optional[str] = None

    # Character encoding (e.g., "utf-8")
    charset: Optional[str] = None

    # Original filename (e.g., "document.pdf")
    filename: Optional[str] = None

    # Local file path (e.g., "/path/to/document.pdf")
    local_path: Optional[str] = None

    # URL (not used in local-only mode, kept for compatibility)
    url: Optional[str] = None

    def copy_and_update(self, **kwargs) -> "StreamInfo":
        """Create a copy with updated fields."""
        current_dict = {
            "mimetype": self.mimetype,
            "extension": self.extension,
            "charset": self.charset,
            "filename": self.filename,
            "local_path": self.local_path,
            "url": self.url,
        }
        current_dict.update(kwargs)
        # Remove None values to keep original values
        current_dict = {k: v for k, v in current_dict.items() if v is not None}
        return StreamInfo(**current_dict)

    def with_extension(self, ext: str) -> "StreamInfo":
        """Create a copy with a new extension."""
        if not ext.startswith("."):
            ext = "." + ext
        return self.copy_and_update(extension=ext)

    def with_mimetype(self, mime: str) -> "StreamInfo":
        """Create a copy with a new MIME type."""
        return self.copy_and_update(mimetype=mime)

    def with_charset(self, charset: str) -> "StreamInfo":
        """Create a copy with a new charset."""
        return self.copy_and_update(charset=charset)