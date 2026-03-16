# MarkDowner User Guide (Current)

MarkDowner is a local CLI tool that converts many document/file types into Markdown.

---

## Quick Start

### 1) Activate environment

Project-local venv:
```bash
cd ~/Projects/MarkDowner
source .venv/bin/activate
```

### 2) Verify
```bash
python -m markdowner --version
```

---

## Basic Usage

### Convert file to stdout
```bash
python -m markdowner input.pdf
```

### Convert file to markdown output file
```bash
python -m markdowner input.docx -o output.md
```

### Convert from stdin with extension hint
```bash
cat input.rtf | python -m markdowner -x .rtf > output.md
```

### Convert from redirected stdin
```bash
python -m markdowner -x .txt < notes.txt
```

---

## Supported Formats

- Text: `.txt`
- Rich Text: `.rtf`
- HTML: `.html`, `.htm`
- CSV: `.csv`
- PDF: `.pdf`
- Word: `.docx`
- PowerPoint: `.pptx`
- Excel: `.xlsx`, `.xls`
- EPUB: `.epub`
- Outlook: `.msg`
- Images: `.jpg`, `.jpeg`, `.png`
- Audio: `.wav`, `.mp3`, `.m4a`, `.mp4`
- Archives: `.zip` (recursive conversion for supported inner files)

---

## Outlook MSG + Attachment Behavior

When converting `.msg`:
- Main email body is converted to markdown.
- Attachments are inspected and, if supported, converted through the normal converter pipeline.
- If you pass `-o output.md`, attachment markdown files are written as sibling files.

Example output naming:
- `output.md` (main message)
- `output-attachment-<name>.md`
- `output-attachment-2-<name>.md` (additional attachments)

If an attachment cannot be converted:
- Main message conversion still succeeds.
- A concise warning is printed to stderr.

---

## Output Path Rules

- `-o/--output` expects a file path.
- Directory targets are rejected (including trailing `/` directory hints).
- Parent directories for output files are created automatically when needed.

---

## Dependencies

Install with all optional converters:
```bash
pip install -e ".[all]"
```

Optional/recommended for image metadata:
```bash
brew install exiftool
```

---

## Troubleshooting

### “is a directory” output error
You passed a directory to `-o`. Provide a full output file path, e.g. `-o result.md`.

### Attachment warnings during MSG conversion
Warnings like `attachment skipped (...)` mean attachment conversion failed or was unsupported. Main message output remains valid.

### Converter dependency missing
Install relevant extras (e.g. `.[pdf]`, `.[docx]`, `.[xls]`, `.[all]`).

### Wrong Python/venv
```bash
which python
python -V
```
Ensure it points to your intended venv.

---

## Current Validation Status

Latest local full test run:
```bash
.venv/bin/python -m pytest -q
```
Result:
- **145 passed**

---

## Safety Notes

- Local-first tool; no default remote URL conversion flow.
- Input and ZIP limits are enforced.
- For untrusted files, keep default limits and run in controlled environments.
