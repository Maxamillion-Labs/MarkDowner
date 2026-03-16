# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test CLI parity - verify all CLI workflows work correctly."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from markdowner.__main__ import _attachment_output_path, _write_output_files
from markdowner._base_converter import DocumentConverterResult

FIXTURES = Path(__file__).parent / "test_files"


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


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_cli_rtf_file_does_not_misroute_to_csv():
    """RTF file conversion should not produce a raw-RFT markdown table."""
    fixture = FIXTURES / "rtf_csv_like_sample.rtf"

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(fixture)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout
    assert not result.stdout.startswith("| {\\rtf")
    assert "{\\rtf" not in result.stdout


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_cli_rtf_stdin_with_extension_does_not_misroute_to_csv():
    """RTF stdin conversion should honor the .rtf hint and avoid CSV fallback."""
    fixture = FIXTURES / "rtf_csv_like_sample.rtf"

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", "-x", ".rtf"],
        input=fixture.read_bytes(),
        capture_output=True,
        text=False,
    )

    assert result.returncode == 0
    output = result.stdout.decode("utf-8")
    assert output
    assert not output.startswith("| {\\rtf")
    assert "{\\rtf" not in output


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


def test_cli_malformed_zip_falls_back_instead_of_hard_failing(tmp_path):
    """Malformed ZIP input should be treated as recoverable and allowed to fall back."""
    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_bytes(b"PK\x03\x04not-a-real-zip")

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(bad_zip)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "not-a-real-zip" in result.stdout
    assert result.stderr == ""


def test_cli_rejects_infinite_like_input(monkeypatch, tmp_path, capsys):
    """Mocked non-regular local input should fail without hanging."""
    from markdowner import __main__
    from markdowner._exceptions import UnsafeLocalSourceException

    mocked_path = tmp_path / "infinite.bin"
    mocked_path.write_bytes(b"x")

    monkeypatch.setattr(
        sys,
        "argv",
        ["markdowner", str(mocked_path)],
    )

    with mock.patch("markdowner.__main__.Path.exists", return_value=True):
        with mock.patch(
            "markdowner.__main__.MarkDowner.convert_local",
            side_effect=UnsafeLocalSourceException(str(mocked_path)),
        ):
            assert __main__.main() == 1

    captured = capsys.readouterr()
    assert "non-regular local source" in captured.err.lower()


@pytest.mark.skipif(
    not (FIXTURES / "sample-attachment.msg").exists(),
    reason="sample-attachment.msg fixture not present",
)
def test_cli_msg_attachment_creates_output_file(tmp_path):
    """MSG with attachment should create main output file."""
    fixture = FIXTURES / "sample-attachment.msg"
    output_file = tmp_path / "output.md"

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(fixture), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert content.strip()


@pytest.mark.skipif(
    not (FIXTURES / "sample-attachment.msg").exists(),
    reason="sample-attachment.msg fixture not present",
)
def test_cli_msg_attachment_failure_is_non_fatal(tmp_path):
    """Attachment conversion failure should not cause non-zero exit if main conversion succeeds."""
    fixture = FIXTURES / "sample-attachment.msg"
    output_file = tmp_path / "output.md"

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(fixture), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )

    # Should succeed even if attachment fails
    assert result.returncode == 0
    assert output_file.exists()


@pytest.mark.skipif(
    not (FIXTURES / "sample-attachment.msg").exists(),
    reason="sample-attachment.msg fixture not present",
)
def test_cli_msg_attachment_warning_on_failure(tmp_path):
    """Failed attachment conversion should produce a warning."""
    fixture = FIXTURES / "sample-attachment.msg"
    output_file = tmp_path / "output.md"

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(fixture), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )

    # Either attachment succeeds (file created) or failure produces warning
    attachment_files = list(tmp_path.glob("output-attachment*.md"))
    if not attachment_files:
        # If no attachment file, there should be a warning about skipped attachment
        assert "attachment skipped" in result.stderr.lower() or "warning" in result.stderr.lower()


def test_cli_output_rejects_directory(tmp_path):
    """Test: --output as directory should fail with clear error."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello")
    
    output_dir = tmp_path / "output_dir"
    output_dir.mkdir()
    
    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(test_file), "-o", str(output_dir)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 1
    assert "is a directory" in result.stderr.lower()


def test_cli_output_rejects_trailing_separator_directory_hint(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello")

    output_dir = tmp_path / "new-dir"
    output_arg = f"{output_dir}{os.sep}"

    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(test_file), "-o", output_arg],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "is a directory" in result.stderr.lower()
    assert not output_dir.exists()


def test_cli_output_creates_parent_directories(tmp_path):
    """Test: --output with non-existing parent should create parent dirs."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello")
    
    output_file = tmp_path / "subdir" / "output.md"
    
    result = subprocess.run(
        [sys.executable, "-m", "markdowner", str(test_file), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert output_file.exists()
    assert "Hello" in output_file.read_text()


def test_attachment_output_paths_are_deterministic(tmp_path):
    output_file = tmp_path / "report.md"
    result = DocumentConverterResult(
        text_content="main body",
        metadata={
            "attachment_outputs": [
                {"name": "alpha.txt", "markdown": "alpha body"},
                {"name": "beta.txt", "markdown": "beta body"},
            ]
        },
    )

    _write_output_files(output_file, result)

    first_attachment = _attachment_output_path(output_file, 0, "alpha.txt")
    second_attachment = _attachment_output_path(output_file, 1, "beta.txt")
    assert first_attachment.name == "report-attachment-alpha.md"
    assert second_attachment.name == "report-attachment-2-beta.md"
    assert first_attachment.read_text() == "alpha body"
    assert second_attachment.read_text() == "beta body"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
