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
import io
import sys
from pathlib import Path

from ._core import MarkDowner
from ._stream_info import StreamInfo
from ._exceptions import MarkDownerException


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

            stdin_data = md._read_stream_with_limit(sys.stdin.buffer)

            if stdin_data.getbuffer().nbytes == 0:
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

            result = md.convert(stdin_data, stream_info=stream_info)

    except MarkDownerException as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    # Output result
    if args.output:
        Path(args.output).write_text(result.text_content, encoding="utf-8")
    else:
        print(result.text_content, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
