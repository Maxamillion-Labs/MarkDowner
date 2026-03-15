# MarkDowner Specification (As-Built)

Date: 2026-03-15  
Project: `~/Projects/MarkDowner`  
Package: `markdowner`  
Version: `1.0.0`

---

## 1) Purpose

MarkDowner is a local, CLI-first document-to-Markdown converter.

Primary goal:
- Convert local files and stdin streams to Markdown using one consistent CLI.

Secondary goals:
- Keep attack surface low (no server mode, no network fetch path in core flow).
- Enforce practical resource controls for untrusted input.

---

## 2) Current Product Scope

### In scope (implemented)
- Local file conversion (`markdowner <file>`)
- Stdin conversion (`cat file | markdowner -x .ext`)
- Output to stdout or `-o/--output`
- Extension / MIME / charset hints

### Out of scope (intentionally)
- MCP/server mode
- Remote URL conversion (`http/https/data/file` URI ingestion)
- Cloud doc-intel style integrations
- Implicit plugin marketplace loading

---

## 3) CLI Contract (implemented)

Command:
- `markdowner [filename]`

Args:
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

---

## 4) Converter Coverage (current)

| Format | Status | Backend/Path |
|---|---|---|
| TXT / generic text | ✅ | plain text converter |
| HTML | ✅ | BeautifulSoup + markdownify path |
| CSV | ✅ | pandas-based table conversion |
| PDF | ✅ | pdfminer/pdfplumber path |
| DOCX | ✅ | mammoth + markdown pipeline |
| PPTX | ✅ | python-pptx |
| XLSX | ✅ | pandas + openpyxl |
| XLS | ✅ | pandas + xlrd |
| EPUB | ✅ | ebooklib |
| MSG (Outlook) | ✅ | olefile path |
| Images | ✅ | EXIF metadata path (+ ExifTool guard) |
| Audio | ✅ | pydub / speech-recognition path |
| ZIP | ✅ | recursive conversion with streaming limits |
| RTF | ✅ | **pandoc subprocess** (`-f rtf -t gfm`) |

Notes:
- RTF conversion uses external binary `pandoc` (non-interactive subprocess call).
- ZIP processing includes nested handling with recursion/decompression limits.

---

## 5) Security Controls (implemented)

1. **Bounded read controls**
   - Input-size enforcement for local and stdin streams.

2. **Unsafe local source rejection**
   - Non-regular local sources are rejected in local-file path.

3. **ZIP protections**
   - Entry count limit
   - Per-entry decompressed byte limit
   - Total decompressed byte limit
   - Recursion depth limit
   - Streaming enforcement of decompressed-byte limits

4. **Bounded ZIP package detection**
   - DOCX/PPTX/XLSX/EPUB signature checks are bounded.

5. **Parser isolation hooks**
   - Heavy parser paths use subprocess timeout/failure handling via internal sandbox helper.

6. **Temp-file hygiene**
   - TemporaryDirectory-based lifecycle for conversion temp artifacts (normal-exit cleanup).

7. **ExifTool version guard**
   - Enforces minimum safe ExifTool version (`>= 12.24`) before EXIF extraction.

---

## 6) Dependencies

## Python requirement
- `>=3.10`

## Base deps (always)
- beautifulsoup4
- markdownify
- magika
- charset-normalizer

## Optional extras
- `pdf`: pdfminer.six, pdfplumber
- `docx`: mammoth, lxml
- `pptx`: python-pptx
- `xlsx`: pandas, openpyxl, tabulate
- `xls`: pandas, xlrd
- `outlook`: olefile
- `audio`: pydub, SpeechRecognition
- `epub`: ebooklib

## External binary
- `pandoc` (required for RTF conversion)
  - macOS install: `brew install pandoc`

### Important packaging note
Current `all` extra in `pyproject.toml` omits `tabulate`.  
For broad install, use:
```bash
pip install -e ".[all]" tabulate
```

---

## 7) Current Validation Snapshot

Recent local validation in project venv:
```bash
source .venv/bin/activate
python -m pytest tests/ -q
```
Result observed: `72 passed` (last verified 2026-03-15).

---

## 8) Known Limitations

1. RTF output quality is bounded by Pandoc’s RTF reader behavior and input document structure.
2. Very large/complex documents may hit subprocess timeout thresholds.
3. Temp artifacts are cleaned on normal exit; abrupt kill/power-loss can leave residue.
4. Memory hard caps depend partly on platform capability for resource limits.

---

## 9) Non-Goals (still true)

- Real-time server/API mode
- Remote web fetch conversion pipeline
- Background autonomous plugin execution

---

## 10) Operational Recommendation

Use project-local venv for deterministic runs:
```bash
cd ~/Projects/MarkDowner
source .venv/bin/activate
python -m markdowner --version
```

For user-level shared runtime, use `~/.venvs/markdowner` and explicitly invoke that interpreter.
