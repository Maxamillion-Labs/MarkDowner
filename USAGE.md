# MarkDowner Usage Guide

## CLI Reference

### Basic Usage

```bash
# Convert file to stdout
markdowner input.pdf

# Convert file to output file
markdowner input.pdf -o output.md

# Convert from stdin with -x flag
cat input.pdf | markdowner -x .pdf

# Convert from stdin with shell redirect
markdowner < input.pdf -x .pdf
```

### Command-Line Options

```
markdowner [-h] [--version] [-o OUTPUT] [-x EXTENSION] [-m MIME-TYPE] [-c CHARSET] [filename]

Positional Arguments:
  filename                 Input file path (omit for stdin)

Options:
  -h, --help              Show this help message and exit
  --version               Show version number
  -o OUTPUT, --output OUTPUT
                          Output file path (default: stdout)
  -x EXTENSION, --extension EXTENSION
                          File extension hint for stdin (e.g., .pdf, .docx)
  -m MIME-TYPE, --mime-type MIME-TYPE
                          MIME type hint for stdin (e.g., application/pdf)
  -c CHARSET, --charset CHARSET
                          Character encoding hint (e.g., utf-8)
```

## Programmatic Usage

### Basic Conversion

```python
from markdowner import MarkDowner

md = MarkDowner()
result = md.convert("document.pdf")
print(result.text_content)
```

### With Stream Info

```python
from markdowner import MarkDowner
from markdowner._stream_info import StreamInfo

md = MarkDowner()

# Create stream info with hints
stream_info = StreamInfo(
    extension=".pdf",
    mimetype="application/pdf",
)

result = md.convert("document.pdf", stream_info=stream_info)
```

### With Custom Limits

```python
from markdowner import MarkDowner
from markdowner._limits import create_custom_limits

# Create custom limits
limits = create_custom_limits(
    max_input_bytes=50 * 1024 * 1024,  # 50MB
    max_zip_entries=100,
    max_zip_total_uncompressed_bytes=100 * 1024 * 1024,  # 100MB
)

md = MarkDowner(limits=limits)
result = md.convert("large_file.pdf")
```

### Reading from Stdin

```python
import io
from markdowner import MarkDowner

md = MarkDowner()

# Read from stdin
stdin_data = io.BytesIO(b"input content")
stream_info = StreamInfo(extension=".txt")

result = md.convert(stdin_data, stream_info=stream_info)
print(result.text_content)
```

## Result Object

The `convert()` method returns a `DocumentConverterResult` with:

- `text_content`: The converted Markdown text
- `metadata`: Dictionary with conversion metadata
- `warnings`: List of warnings from the conversion

```python
result = md.convert("document.pdf")
print(result.text_content)
print(result.metadata)
print(result.warnings)
```

## Exit Codes

- `0` - Success
- `1` - Error (file not found, unsupported format, conversion failed)

## Examples

### Convert a DOCX file

```bash
markdowner report.docx -o report.md
```

### Convert from pipe

```bash
cat spreadsheet.xlsx | markdowner -x .xlsx
```

### Batch processing

```bash
for file in *.pdf; do
    markdowner "$file" -o "${file%.pdf}.md"
done
```

### Check file type automatically

```bash
# MarkDowner uses magika to detect file types
# You can also provide hints via -m or -x
file.pdf | markdowner -m application/pdf
```