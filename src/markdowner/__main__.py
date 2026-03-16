#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""
MarkDowner CLI entry point.

Supports the following workflows:
- markdowner input.pdf
- markdowner input.pdf -o output.md
- cat input.pdf | markdowner -x .pdf
- markdowner < input.pdf -x .pdf
"""

import argparse
import os
import re
import sys
from pathlib import Path

from ._core import MarkDowner
from ._stream_info import StreamInfo
from ._exceptions import MarkDownerException
from ._base_converter import DocumentConverterResult


def _output_arg_looks_like_directory(value: str) -> bool:
    """Treat existing directories and trailing separators as directory targets."""
    separators = [os.sep]
    if os.altsep:
        separators.append(os.altsep)
    return any(value.endswith(separator) for separator in separators)


def _sanitize_attachment_label(name: str | None) -> str:
    if not name:
        return ""
    stem = Path(name).stem.strip().lower()
    return re.sub(r"[^a-z0-9]+", "-", stem).strip("-")


def _attachment_output_path(output_path: Path, index: int, attachment_name: str | None = None) -> Path:
    sequence_suffix = "" if index == 0 else f"-{index + 1}"
    label = _sanitize_attachment_label(attachment_name)
    label_suffix = f"-{label}" if label else ""
    return output_path.with_name(
        f"{output_path.stem}-attachment{sequence_suffix}{label_suffix}.md"
    )


def _write_output_files(output_path: Path, result: DocumentConverterResult) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.text_content, encoding="utf-8")

    for index, attachment in enumerate(result.metadata.get("attachment_outputs", [])):
        _attachment_output_path(output_path, index, attachment.get("name")).write_text(
            attachment["markdown"],
            encoding="utf-8",
        )


def main() -> int:
    """Main entry point for the markdowner CLI."""
    parser = argparse.ArgumentParser(
        prog="markdowner",
        description="Convert local files and stdin to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.pdf                    Convert file to stdout
  %(prog)s input.pdf -o output.md       Convert file to output file
  cat input.pdf | %(prog)s -x .pdf      Convert stdin with extension hint
  %(prog)s < input.pdf -x .pdf          Convert stdin with redirect
        """,
    )

    parser.add_argument(
        "filename",
        nargs="?",
        type=str,
        help="Input file path (omit for stdin)",
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        dest="output",
        help="Output file path (default: stdout)",
    )

    parser.add_argument(
        "-x", "--extension",
        type=str,
        dest="extension",
        help="File extension hint for stdin (e.g., .pdf, .docx)",
    )

    parser.add_argument(
        "-m", "--mime-type",
        type=str,
        dest="mime_type",
        help="MIME type hint for stdin (e.g., application/pdf)",
    )

    parser.add_argument(
        "-c", "--charset",
        type=str,
        dest="charset",
        help="Character encoding hint (e.g., utf-8)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    args = parser.parse_args()

    # Initialize MarkDowner
    md = MarkDowner()

    # Determine input source
    try:
        if args.filename:
            # File path input
            path = Path(args.filename)
            if not path.exists():
                parser.error(f"File not found: {args.filename}")

            # Build stream info
            stream_info = StreamInfo(
                local_path=str(path),
                extension=path.suffix,
                filename=path.name,
            )

            result = md.convert(str(path), stream_info=stream_info)

        else:
            # stdin input
            if sys.stdin.isatty():
                parser.error("No input provided. Use filename or pipe from stdin.")

            stdin_stream = md._coerce_stream_with_limit(sys.stdin.buffer)
            current_pos = stdin_stream.tell()
            stdin_stream.seek(0, 2)
            stdin_size = stdin_stream.tell()
            stdin_stream.seek(current_pos)
            if stdin_size == 0:
                parser.error("Empty stdin input")

            # Build stream info from hints
            extension = args.extension
            if extension and not extension.startswith("."):
                extension = "." + extension

            stream_info = StreamInfo(
                extension=extension,
                mimetype=args.mime_type,
                charset=args.charset,
            )

            result = md.convert_stream(stdin_stream, stream_info=stream_info)

    except MarkDownerException as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    # Output result
    if args.output:
        output_path = Path(args.output)

        if output_path.is_dir() or (
            not output_path.exists() and _output_arg_looks_like_directory(args.output)
        ):
            print(
                f"Error: --output '{args.output}' is a directory. Please specify a file path.",
                file=sys.stderr,
            )
            return 1
        _write_output_files(output_path, result)
    else:
        print(result.text_content, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
