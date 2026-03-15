# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""
Base converter classes for MarkDowner.

Provides the DocumentConverter base class and DocumentConverterResult
for implementing file format converters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, BinaryIO, List, Optional

from ._stream_info import StreamInfo


# Priority constants - lower values are tried first.
PRIORITY_ARCHIVE = -20.0
PRIORITY_RTF = -15.0
PRIORITY_DOC_SPECIFIC = -10.0
PRIORITY_CSV = -5.0
PRIORITY_GENERIC = 10.0

# Backward-compatible aliases for existing converters.
PRIORITY_SPECIFIC_FILE_FORMAT = PRIORITY_DOC_SPECIFIC
PRIORITY_GENERIC_FILE_FORMAT = PRIORITY_GENERIC


@dataclass
class DocumentConverterResult:
    """
    Result of a document conversion.

    Attributes:
        text_content: The converted Markdown text.
        metadata: Additional metadata about the conversion.
        warnings: List of warnings from the conversion.
    """

    text_content: str = ""
    metadata: dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        self.metadata[key] = value


class DocumentConverter(ABC):
    """
    Abstract base class for document converters.

    Subclass this to implement conversion for a specific file format.
    """

    # Priority for this converter (lower = tried first)
    priority: float = PRIORITY_SPECIFIC_FILE_FORMAT

    @abstractmethod
    def accepts(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> bool:
        """
        Determine if this converter can handle the given stream.

        Args:
            stream: The file stream to check.
            stream_info: Metadata about the stream.
            **kwargs: Additional arguments.

        Returns:
            True if this converter can handle the stream, False otherwise.
        """
        pass

    @abstractmethod
    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs
    ) -> DocumentConverterResult:
        """
        Convert the stream to Markdown.

        Args:
            stream: The file stream to convert.
            stream_info: Metadata about the stream.
            **kwargs: Additional arguments.

        Returns:
            DocumentConverterResult containing the Markdown text.
        """
        pass

    @property
    def name(self) -> str:
        """Return the converter name for logging/debugging."""
        return self.__class__.__name__


class SkipConversionException(Exception):
    """Exception raised when a converter wants to skip processing."""

    def __init__(self, reason: str = ""):
        self.reason = reason
        super().__init__(f"Skipped: {reason}")


class FailedConversionException(Exception):
    """Exception raised when a converter fails to process a file."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
