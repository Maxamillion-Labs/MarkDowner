# MarkDowner User Guide

MarkDowner is a local CLI tool that converts many document/file types into Markdown.

## What it does

- Converts local files to Markdown
- Converts piped stdin to Markdown
- Supports output to stdout or a file
- Handles multiple formats through one command

---

## Quick Start

## 1) Activate environment

### Option A (project-local venv)
```bash
cd ~/Projects/MarkDowner
source .venv/bin/activate
```

### Option B (user-level shared venv)
```bash
source ~/.venvs/markdowner/bin/activate
```

## 2) Verify install
```bash
python -m markdowner --version
```

---

## Basic Usage

## Convert a file to stdout
```bash
python -m markdowner input.pdf
```

## Convert a file to an output file
```bash
python -m markdowner input.docx -o output.md
```

## Convert from stdin (pipe) with extension hint
```bash
cat input.rtf | python -m markdowner -x .rtf > output.md
```

## Convert from redirected stdin
```bash
python -m markdowner -x .txt < notes.txt
```

## Show CLI help
```bash
python -m markdowner --help
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

## Dependencies

MarkDowner uses optional Python dependencies for some formats plus external tools.

## External tools

### Required for RTF
```bash
brew install pandoc
```

### Recommended for image metadata extraction
```bash
brew install exiftool
```

## Python dependencies
If installing from project extras:
```bash
pip install -e ".[all]" tabulate
```

> Note: `tabulate` is needed for table rendering and should be included explicitly.

---

## Practical Examples

## RTF to Markdown
```bash
python -m markdowner "/Users/max/Dropbox/Documents/Financial-Analysis-Draft.rtf" -o "/Users/max/Dropbox/Documents/Financial-Analysis-Draft.md"
```

## Convert DOCX and save beside original
```bash
python -m markdowner report.docx -o report.md
```

## Convert ZIP of mixed files
```bash
python -m markdowner documents.zip -o documents.md
```

---

## Troubleshooting

## “pandoc is required for RTF conversion”
Install Pandoc:
```bash
brew install pandoc
```

## “ExifTool not configured” warning
Optional: install ExifTool
```bash
brew install exiftool
```

## Output looks rough for some RTF files
- RTF conversion quality depends on Pandoc + source document complexity
- Try exporting source to DOCX first, then convert DOCX if needed

## Command not found / wrong Python
Ensure you are in the intended venv:
```bash
which python
python -V
```

---

## Safety Notes

- MarkDowner is local-first (no built-in remote URL conversion path)
- Input and ZIP limits are enforced to reduce resource abuse risk
- For untrusted files, keep using current security defaults and run in controlled environments

---

## Recommended Workflow

1. Activate venv
2. Run conversion command
3. Inspect resulting `.md`
4. If needed, run a cleanup/edit pass on markdown for readability

---

## One-liner launcher (optional)

If you want a permanent shortcut:
```bash
cat > ~/bin/markdowner <<'EOF'
#!/usr/bin/env bash
source ~/.venvs/markdowner/bin/activate
python -m markdowner "$@"
EOF
chmod +x ~/bin/markdowner
```

Then use:
```bash
markdowner input.docx -o output.md
```
