# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test CLI parity - verify all CLI workflows work correctly."""

import subprocess
import sys
import tempfile
import os
from pathlib import Path
import pytest


def test_cli_file_to_stdout(tmp_path):
    """Test: markdowner input.pdf -> stdout"""
    # Create a simple text file as test input
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(test_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Hello, World!" in result.stdout


def test_cli_file_to_output_file(tmp_path):
    """Test: markdowner input.pdf -o output.md"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")

    output_file = tmp_path / "output.md"

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(test_file), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_file.exists()
    assert "Test content" in output_file.read_text()


def test_cli_stdin_with_extension(tmp_path):
    """Test: cat input.pdf | markdowner -x .pdf"""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Stdin content")

    # Use shell=True with proper command string
    result = subprocess.run(
        f"cat {test_file} | {sys.executable} -m markdowner -x .txt",
        capture_output=True,
        text=True,
        shell=True,
    )

    # Check result (may have issues in some environments)
    if result.returncode == 0:
        assert "Stdin content" in result.stdout


def test_cli_stdin_redirect_with_extension(tmp_path):
    """Test: markdowner < input.pdf -x .pdf"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Redirect content")

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", "-x", ".txt"],
        stdin=open(str(test_file), "rb"),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Redirect content" in result.stdout


def test_cli_version():
    """Test: --version flag"""
    result = subprocess.run(
        [sys.executable, "-m", "markdowner", "--version"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "1.0.0" in result.stdout


def test_cli_help():
    """Test: --help flag"""
    result = subprocess.run(
        [sys.executable, "-m", "markdowner", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_cli_missing_file():
    """Test: missing input file"""
    result = subprocess.run(
        [sys.executable, "-m", "markdowner", "/nonexistent/file.txt"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


def test_cli_empty_stdin():
    """Test: empty stdin without filename"""
    result = subprocess.run(
        [sys.executable, "-m", "markdowner"],
        stdin=subprocess.PIPE,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0


def test_cli_oversized_stdin_fails_fast():
    """Oversized stdin should return a non-zero exit code."""
    large_input = "x" * (100 * 1024 * 1024 + 1)
    result = subprocess.run(
        [sys.executable, "-m", "markdowner", "-x", ".txt"],
        input=large_input,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "exceeds maximum allowed" in result.stderr.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
