# Baseline Documentation

## Overview

This document captures the baseline behavior and expected outputs for MarkDowner, serving as a reference for regression testing and parity verification.

## Baseline Test Files

The following fixture files are used for baseline testing. Each should produce consistent Markdown output.

### Text Files

| File | Extension | Expected Behavior |
|------|-----------|-------------------|
| plain.txt | .txt | Direct text content |
| utf8.txt | .txt | UTF-8 encoded text |
| utf16.txt | .txt | UTF-16 encoded text |
| empty.txt | .txt | Empty output |

### HTML Files

| File | Extension | Expected Behavior |
|------|-----------|-------------------|
| simple.html | .html | Extracted text content |
| with-styles.html | .html | Style tags removed |
| with-scripts.html | .html | Script tags removed |

### Office Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| DOCX | .docx | Via mammoth |
| XLSX | .xlsx | Via pandas |
| PPTX | .pptx | Via python-pptx |
| PDF | .pdf | Via pdfminer |
| MSG | .msg | Via olefile |

### Archives

| Format | Extension | Notes |
|--------|-----------|-------|
| ZIP | .zip | With limits |
| EPUB | .epub | Via ebook-lib |

### Media

| Format | Extension | Notes |
|--------|-----------|-------|
| Images | .jpg, .png | EXIF metadata only |
| Audio | .mp3, .wav | Metadata only |

## Baseline CLI Workflows

### Workflow 1: File to stdout
```bash
markdowner input.pdf
```
Expected: Markdown output to stdout, exit code 0

### Workflow 2: File to output file
```bash
markdowner input.pdf -o output.md
```
Expected: Markdown saved to output.md, exit code 0

### Workflow 3: Stdin with extension flag
```bash
cat input.pdf | markdowner -x .pdf
```
Expected: Markdown output to stdout, exit code 0

### Workflow 4: Stdin with redirect
```bash
markdowner < input.pdf -x .pdf
```
Expected: Markdown output to stdout, exit code 0

## Expected Error Cases

| Input | Expected Error |
|-------|----------------|
| Nonexistent file | Error message with "not found" |
| Empty stdin | Error message about empty input |
| Unsupported format | UnsupportedFormatException |
| Oversized input | InputSizeExceededException |
| Oversized ZIP | ZipLimitExceededException |

## Security Baseline

| Limit | Default Value | Can Be Disabled |
|-------|----------------|-----------------|
| max_input_bytes | 100 MB | Yes |
| max_zip_entries | 1,000 | Yes |
| max_zip_total_uncompressed_bytes | 200 MB | Yes |
| max_zip_entry_bytes | 50 MB | Yes |
| max_recursion_depth | 3 | Yes |

## Parity Expectations

When comparing MarkDowner to MarkItDown outputs:

- **Text content should match** - The actual content extracted
- **Whitespace may differ** - Line ending normalization varies
- **Metadata may differ** - No LLM captions in MarkDowner
- **Errors will differ** - Network errors won't occur in MarkDowner

### Content Equivalence Test

Test for content equivalence:

```python
# Extract text and normalize
def normalize(text):
    import re
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Compare normalized content
assert normalize(md_result.text_content) == normalize(ref_text)
```

## Version Information

- MarkDowner Version: 1.0.0
- Python Version: 3.10+
- Core Dependencies: beautifulsoup4, markdownify, magika, charset-normalizer, defusedxml

## Maintenance

Baseline should be updated when:
1. New converters added
2. Converter behavior changes
3. Dependencies updated
4. Security limits modified

Run baseline tests before release:
```bash
pytest tests/test_conversion_parity.py
pytest tests/test_cli_parity.py
```