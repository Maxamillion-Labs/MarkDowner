# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""MarkDowner - CLI-first local document-to-Markdown converter."""

__version__ = "1.0.0"

from ._core import MarkDowner
from ._base_converter import DocumentConverterResult, DocumentConverter
from ._stream_info import StreamInfo
from ._exceptions import (
    MarkDownerException,
    MissingDependencyException,
    FailedConversionAttempt,
    FileConversionException,
    UnsupportedFormatException,
    InputSizeExceededException,
    ZipLimitExceededException,
)
from ._limits import Limits

__all__ = [
    "__version__",
    "MarkDowner",
    "DocumentConverter",
    "DocumentConverterResult",
    "MarkDownerException",
    "MissingDependencyException",
    "FailedConversionAttempt",
    "FileConversionException",
    "UnsupportedFormatException",
    "InputSizeExceededException",
    "ZipLimitExceededException",
    "StreamInfo",
    "Limits",
]