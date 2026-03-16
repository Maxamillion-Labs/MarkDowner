# MarkDowner 🤖📄➡️📝

A **local-only, reliable, security-focused** CLI that converts documents and streams to Markdown for automation and AI workflows.

MarkDowner is forked from Microsoft’s **MarkItDown** concept and reshaped for a different mission: deterministic local execution, stronger safety defaults, and cleaner behavior for pipelines/agents.

---

## Why MarkDowner 🚀

Why fork away from MarkItDown-style defaults:
- 🔒 **Local-only trust boundary** — no built-in remote fetch path in the core flow
- 🛡️ **Security controls first** — input limits, ZIP limits, recursion limits, unsafe source rejection
- ⚙️ **Automation-friendly behavior** — stable CLI for file input, stdin/stdout, and output files
- 🤖 **AI workflow ready** — predictable markdown conversion for agent/tool pipelines
- 📦 **One CLI for many formats** — PDF, Office docs, HTML, CSV, ZIP, MSG, and more

---

## Current State (as of 2026-03-15)

- Package: `markdowner`
- Version: `1.0.0`
- Python: `>=3.10`
- Positioning: **local-only, reliable, secure conversion engine**
- Test status (project `.venv`):
  - `.venv/bin/python -m pytest -q`
  - **145 passed**

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

Recommended for richer image metadata handling: install **ExifTool**.

#### macOS (Homebrew)

```bash
brew install exiftool
```

#### Linux

**Debian/Ubuntu**
```bash
sudo apt-get update
sudo apt-get install -y libimage-exiftool-perl
```

**Fedora/RHEL**
```bash
sudo dnf install -y perl-Image-ExifTool
```

#### Windows

Install ExifTool and ensure it is on `PATH`, then verify:

```powershell
exiftool -ver
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

RTF conversion is native-only:

- Lexer/parser/IR/renderer pipeline in `src/markdowner/converters/_rtf_*`
- No subprocess or external converter invocation for `.rtf`
- `.rtf` inputs are routed to the dedicated RTF converter before CSV/generic text probes
- Controlled conversion errors are returned for malformed/unsupported RTF

Known limitations (v1 native parser):

- Focused on common controls (`par`, `line`, `tab`, `b`, `i`, `ul`, `uN`) and basic destination skipping
- Advanced tables, embedded objects, and uncommon control words may render as plain text or be skipped
- For heavily stylized enterprise exports, some manual markdown cleanup may still be needed

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
