# MarkDowner

MarkDowner is a local CLI for converting files and stdin streams to Markdown.

## Verified Controls

- Read-time input size enforcement for local files and stdin
- Explicit rejection of non-regular local sources
- ZIP streaming limits enforced on actual decompressed bytes
- Bounded ZIP package detection for DOCX/PPTX/XLSX/EPUB routing
- Parser subprocess timeout and worker-failure handling
- TemporaryDirectory-scoped temp cleanup on normal exit

## Verified Commands

- `python3 -m pytest tests/ -v`
- `python3 -m pytest tests/test_security_limits.py -v`
- `python3 -m pytest tests/test_zip_behavior.py -v`
- `python3 -m pytest tests/test_security_regressions.py -v`
- `python3 -m markdowner --help`
- `python3 -m markdowner --version`

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
