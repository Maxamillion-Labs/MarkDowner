# MarkDowner Specification (Current As-Built)

Date: 2026-03-15  
Project: `~/Projects/MarkDowner`  
Package: `markdowner`  
Version: `1.0.0`

---

## 1) Purpose

MarkDowner is a local, CLI-first document-to-Markdown converter.

Primary goals:
- Convert local files and stdin streams to Markdown using one consistent CLI.
- Keep execution local and predictable.
- Enforce practical safety limits for untrusted inputs.

---

## 2) Current Product Scope

### In scope (implemented)
- Local file conversion (`markdowner <file>`)
- Stdin conversion (`cat file | markdowner -x .ext`)
- Output to stdout or `-o/--output`
- Extension / MIME / charset hints
- Recursive ZIP conversion for supported embedded types
- Outlook MSG conversion with attachment handling

### Out of scope (intentional)
- Server/API mode
- Remote URL ingestion in the core path
- Cloud doc-intel integrations
- Dynamic plugin marketplace loading

---

## 3) CLI Contract (implemented)

Command:
- `markdowner [filename]`

Arguments:
- `-o, --output <path>`
- `-x, --extension <.ext>`
- `-m, --mime-type <type/subtype>`
- `-c, --charset <encoding>`
- `--version`

Supported workflows:
1. `markdowner input.pdf`
2. `markdowner input.pdf -o output.md`
3. `cat input.pdf | markdowner -x .pdf`
4. `markdowner < input.pdf -x .pdf`

Exit behavior:
- `0` on success
- `1` on controlled conversion/validation errors

Additional current behavior:
- `--output` rejects directory targets (including trailing-separator directory hints).
- For MSG attachments converted to markdown, additional sibling output files are written with deterministic names.

---

## 4) Converter Coverage (current)

| Format | Status | Notes |
|---|---|---|
| TXT / generic text | ✅ | Plain text converter |
| HTML | ✅ | BeautifulSoup + markdownify |
| CSV | ✅ | Structured table conversion |
| PDF | ✅ | pdfminer/pdfplumber path |
| DOCX | ✅ | mammoth path |
| PPTX | ✅ | python-pptx |
| XLSX | ✅ | pandas + openpyxl |
| XLS | ✅ | pandas + xlrd |
| EPUB | ✅ | ebooklib |
| MSG (Outlook) | ✅ | olefile + attachment handling |
| Images | ✅ | Metadata path + ExifTool guard |
| Audio | ✅ | Optional audio converter path |
| ZIP | ✅ | Recursive conversion with limits |
| RTF | ✅ | Native lexer/parser path |

MSG attachment behavior (current):
- Extracts MSG body + attachments where available.
- Attempts attachment conversion via normal MarkDowner pipeline.
- Supported attachment types output markdown sibling files.
- Unsupported/failed attachment conversion is non-fatal and emitted as simple warnings.
- Embedded Outlook item attachments are detected and reported as unsupported.

---

## 5) Security and Reliability Controls (current)

Implemented controls:
1. Input size enforcement (local + stream paths)
2. Rejection of unsafe/non-regular local sources
3. ZIP entry/decompressed-size/recursion limits
4. Bounded archive signature handling
5. Parser subprocess timeout/memory controls
6. Temporary artifact hygiene via scoped temp dirs
7. ExifTool minimum safe version guard (`>= 12.24`)
8. Narrowed conversion fallback policy:
   - Fallback only for explicitly recoverable failures or parser sandbox failures
   - Optional strict mode disables fallback
9. Sandbox IPC deadlock hardening for larger payloads

---

## 6) Dependencies

Python requirement:
- `>=3.10`

Base deps:
- beautifulsoup4
- markdownify
- magika
- charset-normalizer

Extras:
- `pdf`: pdfminer.six, pdfplumber
- `docx`: mammoth, lxml
- `pptx`: python-pptx
- `xlsx`: pandas, openpyxl, tabulate
- `xls`: pandas, xlrd, tabulate
- `outlook`: olefile
- `audio`: pydub, SpeechRecognition
- `epub`: ebooklib

External binary (optional but recommended for image metadata):
- `exiftool`

---

## 7) Validation Snapshot

Most recent local validation:
```bash
.venv/bin/python -m pytest -q
```
Result:
- **145 passed** (verified 2026-03-15)

---

## 8) Known Limitations

1. Advanced/rare RTF constructs may still be flattened.
2. Embedded Outlook item attachments in MSG are currently reported unsupported.
3. Conversion quality can vary based on source document quality/export behavior.
4. Hard process termination can still leave temporary OS-level artifacts.

---

## 9) Operational Recommendation

Use project-local venv for deterministic runs:
```bash
cd ~/Projects/MarkDowner
source .venv/bin/activate
python -m markdowner --version
```

For CI/optional dependency checks, include extra-specific installs where needed (for example `.[xls]`, `.[all]`).
