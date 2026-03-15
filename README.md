# MarkDowner

MarkDowner is a local CLI for converting files and stdin streams to Markdown.

## Verified Commands

### Command
```bash
python3 -m markdowner --version
```

### Output
```text
markdowner 1.0.0
```

### Command
```bash
python3 -m markdowner sample.txt
```

### Output
```text
Sample text for CLI validation.
```

## Core Behaviors Verified Locally

- Plain text file conversion
- Stdin conversion with `-x`
- Output file writing with `-o`
- HTML to Markdown structure retention
- ZIP routing, deterministic ordering, and recursion-limit warnings
- Input-size limit enforcement for seekable and unseekable input
- CSV decoding with UTF-8 and cp1252 fallback handling

## Optional Converter Dependencies

- `docx`: `mammoth`, `lxml`
- `pptx`: `python-pptx`
- `xlsx`: `pandas`, `openpyxl`
- `xls`: `pandas`, `xlrd`
- `pdf`: `pdfminer.six`, `pdfplumber`
- `epub`: `ebooklib`
- `outlook`: `olefile`

## Repository Evidence

- Test and CLI validation output: `STATUS.md`
- Fixture corpus: `tests/test_files/`
- Final implementation summary: `FINAL-IMPLEMENTATION-REPORT.md`
