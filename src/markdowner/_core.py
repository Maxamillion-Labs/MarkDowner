# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""
Core MarkDowner implementation.

Provides the MarkDowner class that orchestrates document conversion.
"""

import io
import mimetypes
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, List, Optional, Union

import magika
import charset_normalizer

from ._base_converter import DocumentConverter, DocumentConverterResult
from ._bounded_stream import BoundedStream
from ._exceptions import (
    FileConversionException,
    UnsupportedFormatException,
    FailedConversionAttempt,
    InputSizeExceededException,
    MarkDownerException,
    UnsafeLocalSourceException,
)
from ._limits import Limits, DEFAULT_LIMITS
from ._stream_info import StreamInfo


# Priority constants
PRIORITY_SPECIFIC_FILE_FORMAT = 0.0
PRIORITY_GENERIC_FILE_FORMAT = 10.0


@dataclass(frozen=True)
class ConverterRegistration:
    """Registration of a converter with its priority."""

    converter: DocumentConverter
    priority: float


class MarkDowner:
    """
    MarkDowner - CLI-first local document-to-Markdown converter.

    Converts local files and stdin streams to Markdown reliably,
    with minimal attack surface and no server/runtime extras.
    """

    def __init__(
        self,
        limits: Optional[Limits] = None,
        **kwargs,
    ):
        """
        Initialize MarkDowner.

        Args:
            limits: Security limits to apply. Uses DEFAULT_LIMITS if None.
            **kwargs: Additional configuration (currently unused, reserved for future).
        """
        self._limits = limits or DEFAULT_LIMITS
        self._magika = magika.Magika()

        # ExifTool path (optional)
        self._exiftool_path: Optional[str] = kwargs.get("exiftool_path")
        if self._exiftool_path is None:
            import shutil
            candidate = shutil.which("exiftool")
            if candidate:
                self._exiftool_path = os.path.abspath(candidate)

        # Register built-in converters
        self._converters: List[ConverterRegistration] = []
        self._register_builtins()

    def _coerce_stream_with_limit(
        self,
        stream: BinaryIO,
        *,
        chunk_size: int = 8192,
    ) -> BinaryIO:
        """Return a seekable stream, buffering unseekable input with limit checks."""
        if stream.seekable():
            return stream
        return self._read_stream_with_limit(stream, chunk_size=chunk_size)

    def _read_stream_with_limit(
        self,
        stream: BinaryIO,
        *,
        chunk_size: int = 8192,
    ) -> io.BytesIO:
        """Buffer a stream incrementally while enforcing the input-size limit."""
        buffer = io.BytesIO()
        total_bytes = 0

        while True:
            read_size = chunk_size
            if self._limits.enabled:
                remaining = self._limits.max_input_bytes - total_bytes
                read_size = min(chunk_size, max(remaining, 0) + 1)

            chunk = stream.read(read_size)
            if not chunk:
                break

            total_bytes += len(chunk)
            if self._limits.enabled and not self._limits.check_input_size(total_bytes):
                raise InputSizeExceededException(
                    total_bytes,
                    self._limits.max_input_bytes,
                    "size",
                )
            buffer.write(chunk)

        buffer.seek(0)
        return buffer

    def _register_builtins(self) -> None:
        """Register all built-in converters."""

        # Import converters here to avoid circular imports
        from .converters import (
            PlainTextConverter,
            ZipConverter,
            HtmlConverter,
            PdfConverter,
            DocxConverter,
            XlsxConverter,
            XlsConverter,
            PptxConverter,
            ImageConverter,
            AudioConverter,
            OutlookMsgConverter,
            EpubConverter,
            CsvConverter,
        )

        # Register converters - later registrations appear first in priority order
        # Generic converters first (higher priority value = tried later)
        self.register_converter(
            PlainTextConverter(),
            priority=PRIORITY_GENERIC_FILE_FORMAT,
        )
        self.register_converter(
            HtmlConverter(),
            priority=PRIORITY_GENERIC_FILE_FORMAT,
        )

        # Specific format converters (lower priority = tried first)
        self.register_converter(CsvConverter())
        self.register_converter(EpubConverter(limits=self._limits))
        self.register_converter(OutlookMsgConverter())
        self.register_converter(PdfConverter())
        self.register_converter(PptxConverter(limits=self._limits))
        self.register_converter(XlsConverter())
        self.register_converter(XlsxConverter(limits=self._limits))
        self.register_converter(DocxConverter(limits=self._limits))
        self.register_converter(ImageConverter())
        self.register_converter(AudioConverter())
        self.register_converter(ZipConverter(markdowner=self, limits=self._limits))

    def convert(
        self,
        source: Union[str, Path, BinaryIO],
        *,
        stream_info: Optional[StreamInfo] = None,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        """
        Convert a source to Markdown.

        Args:
            source: Local file path, Path object, or BinaryIO stream.
            stream_info: Optional stream metadata.
            **kwargs: Additional arguments to pass to converters.

        Returns:
            DocumentConverterResult with the Markdown content.
        """
        # Local path (string or Path)
        if isinstance(source, (str, os.PathLike)):
            return self.convert_local(source, stream_info=stream_info, **kwargs)
        # Binary stream
        elif hasattr(source, "read") and callable(source.read):
            return self.convert_stream(source, stream_info=stream_info, **kwargs)
        else:
            raise TypeError(
                f"Invalid source type: {type(source)}. Expected str, Path, or BinaryIO."
            )

    def convert_local(
        self,
        path: Union[str, os.PathLike],
        *,
        stream_info: Optional[StreamInfo] = None,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        """Convert a local file."""
        path_str = str(path)

        source_stat = os.stat(path_str)
        if not stat.S_ISREG(source_stat.st_mode):
            raise UnsafeLocalSourceException(path_str)

        if self._limits.enabled and not self._limits.check_input_size(source_stat.st_size):
            raise InputSizeExceededException(
                source_stat.st_size,
                self._limits.max_input_bytes,
                "size",
            )

        # Build base stream info
        base_guess = StreamInfo(
            local_path=path_str,
            extension=os.path.splitext(path_str)[1],
            filename=os.path.basename(path_str),
        )

        # Extend with provided stream info
        if stream_info is not None:
            base_guess = base_guess.copy_and_update(
                mimetype=stream_info.mimetype,
                extension=stream_info.extension,
                charset=stream_info.charset,
                filename=stream_info.filename,
                local_path=stream_info.local_path,
                url=stream_info.url,
            )

        # Convert
        with open(path_str, "rb") as fh:
            bounded_fh: BinaryIO = fh
            if self._limits.enabled:
                bounded_fh = BoundedStream(fh, self._limits.max_input_bytes)
            guesses = self._get_stream_info_guesses(bounded_fh, base_guess)
            return self._convert(bounded_fh, guesses, **kwargs)

    def convert_stream(
        self,
        stream: BinaryIO,
        *,
        stream_info: Optional[StreamInfo] = None,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        """Convert a binary stream."""
        # Build base stream info
        base_guess = StreamInfo()
        if stream_info is not None:
            base_guess = base_guess.copy_and_update(
                mimetype=stream_info.mimetype,
                extension=stream_info.extension,
                charset=stream_info.charset,
                filename=stream_info.filename,
                local_path=stream_info.local_path,
                url=stream_info.url,
            )

        # Check if stream is seekable, if not load into memory incrementally
        stream = self._coerce_stream_with_limit(stream)

        # Check input size
        if self._limits.enabled:
            current_pos = stream.tell()
            stream.seek(0, 2)  # Seek to end
            size = stream.tell()
            stream.seek(current_pos)

            if not self._limits.check_input_size(size):
                raise InputSizeExceededException(
                    size, self._limits.max_input_bytes, "size"
                )

        # Get stream info guesses
        guesses = self._get_stream_info_guesses(stream, base_guess)

        return self._convert(stream, guesses, **kwargs)

    def _convert(
        self,
        file_stream: BinaryIO,
        stream_info_guesses: List[StreamInfo],
        **kwargs,
    ) -> DocumentConverterResult:
        """Internal conversion method."""
        result: Optional[DocumentConverterResult] = None
        accept_warnings: List[str] = []

        # Track failed conversion attempts
        failed_attempts: List[FailedConversionAttempt] = []

        # Sort converters by priority (lower = tried first)
        sorted_registrations = sorted(
            self._converters, key=lambda x: x.priority
        )

        # Remember initial stream position
        cur_pos = file_stream.tell()

        # Try each converter
        for stream_info in stream_info_guesses + [StreamInfo()]:
            for converter_registration in sorted_registrations:
                converter = converter_registration.converter

                # Ensure stream position is correct
                file_stream.seek(cur_pos)

                # Check if converter accepts
                accepts = False
                try:
                    accepts = converter.accepts(
                        file_stream, stream_info, exiftool_path=self._exiftool_path, **kwargs
                    )
                except NotImplementedError:
                    pass
                except Exception as exc:
                    accept_warnings.append(
                        f"{converter.name} accept check failed: {exc}"
                    )

                # Reset position after accepts check
                file_stream.seek(cur_pos)

                # Try conversion if accepted
                if accepts:
                    try:
                        result = converter.convert(
                            file_stream,
                            stream_info,
                            exiftool_path=self._exiftool_path,
                            **kwargs,
                        )
                    except MarkDownerException:
                        raise
                    except Exception as e:
                        failed_attempts.append(
                            FailedConversionAttempt(
                                converter=converter,
                                exc_info=sys.exc_info(),
                            )
                        )
                        raise FileConversionException(attempts=failed_attempts) from e
                    finally:
                        file_stream.seek(cur_pos)

                if result is not None:
                    if (
                        not result.text_content.strip()
                        and result.metadata.get("error")
                    ):
                        failed_attempts.append(
                            FailedConversionAttempt(
                                converter=converter,
                                exc_info=(None, Exception(result.metadata["error"]), None),
                            )
                        )
                        result = None
                        continue

                    # Normalize output
                    result.text_content = "\n".join(
                        [line.rstrip() for line in re.split(r"\r?\n", result.text_content)]
                    )
                    result.text_content = re.sub(r"\n{3,}", "\n\n", result.text_content)
                    result.warnings = accept_warnings + result.warnings
                    return result

        # Report failures
        if failed_attempts:
            raise FileConversionException(attempts=failed_attempts)

        # No converter could handle it
        raise UnsupportedFormatException(
            "Could not convert stream to Markdown. No converter attempted a conversion."
        )

    def register_converter(
        self,
        converter: DocumentConverter,
        *,
        priority: float = PRIORITY_SPECIFIC_FILE_FORMAT,
    ) -> None:
        """Register a converter with a given priority."""
        self._converters.insert(
            0, ConverterRegistration(converter=converter, priority=priority)
        )

    def _get_stream_info_guesses(
        self,
        file_stream: BinaryIO,
        base_guess: StreamInfo,
    ) -> List[StreamInfo]:
        """Generate stream info guesses using magika."""
        guesses: List[StreamInfo] = []

        # Enhance base guess with extension/mimetype
        enhanced_guess = base_guess.copy_and_update()

        if base_guess.mimetype is None and base_guess.extension is not None:
            _m, _ = mimetypes.guess_type(
                "placeholder" + base_guess.extension, strict=False
            )
            if _m is not None:
                enhanced_guess = enhanced_guess.copy_and_update(mimetype=_m)

        if base_guess.mimetype is not None and base_guess.extension is None:
            _e = mimetypes.guess_all_extensions(base_guess.mimetype, strict=False)
            if len(_e) > 0:
                enhanced_guess = enhanced_guess.copy_and_update(extension=_e[0])

        # Use magika to identify
        cur_pos = file_stream.tell()
        try:
            result = self._magika.identify_stream(file_stream)
            if result.status == "ok" and result.prediction.output.label != "unknown":
                # Determine charset if text
                charset = None
                if result.prediction.output.is_text:
                    file_stream.seek(cur_pos)
                    stream_page = file_stream.read(4096)
                    charset_result = charset_normalizer.from_bytes(stream_page).best()
                    if charset_result is not None:
                        charset = charset_result.encoding

                # Get extension
                guessed_extension = None
                if len(result.prediction.output.extensions) > 0:
                    guessed_extension = "." + result.prediction.output.extensions[0]

                # Check compatibility
                compatible = True
                if (
                    base_guess.mimetype is not None
                    and base_guess.mimetype != result.prediction.output.mime_type
                ):
                    compatible = False

                if (
                    base_guess.extension is not None
                    and base_guess.extension.lstrip(".")
                    not in result.prediction.output.extensions
                ):
                    compatible = False

                if compatible:
                    guesses.append(
                        StreamInfo(
                            mimetype=base_guess.mimetype or result.prediction.output.mime_type,
                            extension=base_guess.extension or guessed_extension,
                            charset=base_guess.charset or charset,
                            filename=base_guess.filename,
                            local_path=base_guess.local_path,
                        )
                    )
                else:
                    guesses.append(enhanced_guess)
                    guesses.append(
                        StreamInfo(
                            mimetype=result.prediction.output.mime_type,
                            extension=guessed_extension,
                            charset=charset,
                            filename=base_guess.filename,
                            local_path=base_guess.local_path,
                        )
                    )
            else:
                guesses.append(enhanced_guess)
        finally:
            file_stream.seek(cur_pos)

        return guesses
