# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Custom exceptions for MarkDowner."""


class MarkDownerException(Exception):
    """Base exception for MarkDowner."""
    pass


class RecoverableConversionException(MarkDownerException):
    """Raised by converters that explicitly support fallback to next converter.

    This is an intentional signal that the converter accepts fallback behavior
    when conversion fails, allowing the next converter to attempt conversion.
    Use this only when the converter genuinely supports fallback semantics.
    """
    pass


class MissingDependencyException(MarkDownerException):
    """Raised when a required dependency is not installed."""
    pass


class FailedConversionAttempt(MarkDownerException):
    """Raised when a converter attempts but fails to convert a document."""

    def __init__(self, converter, exc_info):
        self.converter = converter
        self.exc_info = exc_info
        super().__init__(f"Converter {converter} failed: {exc_info[1]}")


class FileConversionException(MarkDownerException):
    """Raised when no converter succeeds but at least one attempted conversion."""

    def __init__(self, attempts: list):
        self.attempts = attempts
        messages = []
        for attempt in attempts:
            if hasattr(attempt, 'exc_info') and attempt.exc_info:
                messages.append(str(attempt.exc_info[1]))
        super().__init__(f"Conversion failed: {'; '.join(messages)}")


class UnsupportedFormatException(MarkDownerException):
    """Raised when no converter can handle the input format."""
    pass


class InputSizeExceededException(MarkDownerException):
    """Raised when input exceeds size limits."""

    def __init__(self, size: int, limit: int, limit_type: str = "size"):
        self.size = size
        self.limit = limit
        self.limit_type = limit_type
        super().__init__(
            f"Input {limit_type} {size} exceeds maximum allowed {limit}"
        )


class UnsafeLocalSourceException(MarkDownerException):
    """Raised when a local path is not a regular file."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Refusing to read non-regular local source: {path}")


class ZipLimitExceededException(MarkDownerException):
    """Raised when ZIP archive exceeds limits."""

    def __init__(self, limit_type: str, actual: int, limit: int):
        self.limit_type = limit_type
        self.actual = actual
        self.limit = limit
        super().__init__(
            f"ZIP {limit_type} {actual} exceeds maximum allowed {limit}"
        )
