# MarkDowner

**MarkDowner** is a CLI-first, local-only document-to-Markdown converter. It converts common file formats to Markdown reliably, with minimal attack surface and no server or network extras.

## Features

- **Local-only conversion** - No network calls, no server mode
- **Security-first** - Input size limits, ZIP entry limits, recursion depth limits
- **CLI-first design** - Simple, predictable command-line interface
- **Broad format support** - PDF, DOCX, PPTX, XLSX, HTML, CSV, EPUB, MSG, images, audio, and more

## Installation

```bash
# Basic installation
pip install markdowner

# With all format support
pip install markdowner[all]

# Or install in development mode
pip install -e ".[all]"
```

## Quick Start

```bash
# Convert a file to stdout
markdowner document.pdf

# Convert a file to a specific output
markdowner document.pdf -o output.md

# Convert from stdin with extension hint
cat document.pdf | markdowner -x .pdf

# Convert from stdin with redirect
markdowner < document.pdf -x .pdf

# Show version
markdowner --version
```

## Supported Formats

| Format | Extension | Status |
|--------|-----------|--------|
| PDF | `.pdf` | ✅ |
| DOCX | `.docx` | ✅ |
| PPTX | `.pptx` | ✅ |
| XLSX | `.xlsx` | ✅ |
| XLS | `.xls` | ✅ |
| HTML | `.html`, `.htm` | ✅ |
| CSV | `.csv` | ✅ |
| Plain Text | `.txt` | ✅ |
| EPUB | `.epub` | ✅ |
| Outlook MSG | `.msg` | ✅ |
| Images | `.jpg`, `.png`, etc. | ✅ |
| Audio | `.mp3`, `.wav`, etc. | ✅ |
| ZIP | `.zip` | ✅ |

## Security

MarkDowner includes built-in security limits:

- **Max input size**: 100MB by default
- **Max ZIP entries**: 1,000 by default
- **Max ZIP uncompressed size**: 200MB by default
- **Max ZIP entry size**: 50MB by default
- **Max recursion depth**: 3 levels by default

These can be customized when using MarkDowner programmatically.

## Requirements

- Python 3.10+
- Core dependencies: beautifulsoup4, markdownify, magika, charset-normalizer, defusedxml
- Optional dependencies for specific formats (see `pyproject.toml`)

## License

MIT License - see LICENSE file for details.