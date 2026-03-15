# MarkDowner

A local-first, security-conscious CLI that converts documents and streams to Markdown.

MarkDowner started as a focused fork concept and is now an implemented, test-covered tool for multi-format conversion with one consistent command surface.

---

## Why MarkDowner

- **One CLI for many formats** (PDF, Office docs, HTML, CSV, ZIP, RTF, etc.)
- **Local-first by default** (no built-in remote URL fetch pipeline)
- **Security controls baked in** (input limits, ZIP limits, recursion limits, unsafe source rejection)
- **Pipeline-friendly UX** (file input, stdin, stdout, output file)
- **RTF support via Pandoc** with non-interactive subprocess execution

---

## Current State (as of 2026-03-15)

- Package: `markdowner`
- Version: `1.0.0`
- Python: `>=3.10`
- Test status (project `.venv`):
  - `python -m pytest tests/ -q`
  - **72 passed**

---

## Supported Formats

| Category | Formats |
|---|---|
| Text | `.txt` |
| Web/Text Markup | `.html`, `.htm`, `.csv` |
| Documents | `.pdf`, `.docx`, `.rtf`, `.epub`, `.msg` |
| Presentations | `.pptx` |
| Spreadsheets | `.xlsx`, `.xls` |
| Media | `.jpg`, `.jpeg`, `.png`, `.wav`, `.mp3`, `.m4a`, `.mp4` |
| Archives | `.zip` (recursive conversion of supported inner files) |

---

## Core Security/Resilience Features

- Read-time input size enforcement for file and stdin paths
- Rejection of unsafe non-regular local sources
- ZIP protections:
  - entry count limits
  - per-entry decompressed byte limits
  - total decompressed byte limits
  - recursion depth limits
- Bounded ZIP package detection for DOCX/PPTX/XLSX/EPUB routing
- Converter timeout/worker-failure handling for heavy parsing paths
- Temp-file scoping with `TemporaryDirectory` lifecycle
- ExifTool minimum-version safety check (`>= 12.24`) when configured

---

## Installation

### 1) Clone

```bash
git clone <your-repo-url> MarkDowner
cd MarkDowner
```

### 2) Create/activate project venv (recommended)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
```

### 3) Install package + optional converters

```bash
pip install -e ".[all]" tabulate
```

> Note: `tabulate` is included explicitly for markdown table rendering.

### 4) Install external tools

Required for `.rtf` conversion:

```bash
brew install pandoc
```

Recommended for richer image metadata handling:

```bash
brew install exiftool
```

---

## Usage

### Convert file to stdout

```bash
python -m markdowner input.pdf
```

### Convert file to output file

```bash
python -m markdowner input.docx -o output.md
```

### Convert from stdin with extension hint

```bash
cat input.rtf | python -m markdowner -x .rtf > output.md
```

### Convert redirected stdin

```bash
python -m markdowner -x .txt < notes.txt
```

### Help / version

```bash
python -m markdowner --help
python -m markdowner --version
```

---

## RTF Conversion Notes

RTF conversion is handled by Pandoc:

- Input: `-f rtf`
- Output: `-t gfm`
- Non-interactive subprocess execution
- Timeout-protected execution path

If Pandoc is missing, MarkDowner returns a clear dependency error.

---

## Project Layout

```text
src/markdowner/
  __main__.py
  _core.py
  _limits.py
  _bounded_stream.py
  _sandbox.py
  converters/
tests/
README.md
MarkDowner-spec.md
USER_GUIDE.md
```

---

## Documentation

- **As-built specification:** `MarkDowner-spec.md`
- **User guide:** `USER_GUIDE.md`

---

## What MarkDowner is not

- Not a server product
- Not a web crawler
- Not a cloud document-intelligence platform

It is intentionally scoped as a reliable local conversion engine.

---

## License

MIT (`LICENSE`)
