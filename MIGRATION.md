# Migration Guide: MarkItDown to MarkDowner

## Overview

MarkDowner is a stripped-down fork of MarkItDown focused on:
- **CLI-first** operation
- **Local-only** conversion (no network/URI paths)
- **Security** with built-in limits
- **Minimal dependencies** (no MCP/server code)

## What's Different

### Removed Features

| Feature | MarkItDown | MarkDowner |
|---------|------------|------------|
| HTTP/HTTPS URI conversion | ✅ | ❌ |
| file:// URI conversion | ✅ | ❌ |
| data:// URI conversion | ✅ | ❌ |
| MCP server mode | ✅ | ❌ |
| SSE/HTTP serving | ✅ | ❌ |
| YouTube converter | ✅ | ❌ |
| Wikipedia converter | ✅ | ❌ |
| Bing SERP converter | ✅ | ❌ |
| Azure Doc Intelligence | ✅ | ❌ |
| Plugin auto-loading | ✅ | ❌ |
| LLM caption hooks | ✅ | ❌ |

### What's the Same

- Core conversion for local files (PDF, DOCX, PPTX, XLSX, HTML, etc.)
- CLI interface patterns
- Converter architecture

## CLI Migration

### Before (MarkItDown)

```bash
# URL conversion
markitdown https://example.com/page.html

# Server mode
markitdown --server

# File conversion
markitdown document.pdf
```

### After (MarkDowner)

```bash
# File conversion only
markdowner document.pdf

# Stdin conversion
cat document.pdf | markdowner -x .pdf
```

The CLI arguments remain the same for file-based operations.

## API Migration

### Before (MarkItDown)

```python
from markitdown import MarkItDown

md = MarkItDown()

# URL conversion
result = md.convert("https://example.com/page.html")

# File conversion
result = md.convert("document.pdf")
```

### After (MarkDowner)

```python
from markdowner import MarkDowner

md = MarkItDown()

# File conversion only
result = md.convert("document.pdf")

# Or from stream
import io
result = md.convert(io.BytesIO(data), stream_info=stream_info)
```

### Removed Methods

- `convert_url()` - Not available
- `convert_uri()` - Not available
- `convert_response()` - Not available
- `enable_plugins()` - Not available

### New/Modified Options

- `MarkDowner(limits=...)` - New security limits parameter
- Stream-first conversion for better security

## Security Changes

### New Limits System

```python
from markdowner import MarkDowner
from markdowner._limits import create_custom_limits

# Custom limits
limits = create_custom_limits(
    max_input_bytes=50 * 1024 * 1024,
    max_zip_entries=100,
)

md = MarkDowner(limits=limits)
```

### Exceptions

New exceptions added:
- `InputSizeExceededException`
- `ZipLimitExceededException`

## Dependency Changes

### Core Dependencies (Required)

```toml
dependencies = [
    "beautifulsoup4>=4.12.0",
    "markdownify>=0.11.0",
    "magika>=0.2.0",
    "charset-normalizer>=3.0.0",
    "defusedxml>=0.7.0",
]
```

### Optional Dependencies (By Format)

```toml
[project.optional-dependencies]
pdf = ["pdfminer.six>=20231228", "pdfplumber>=0.10.0"]
docx = ["mammoth>=1.6.0", "lxml>=5.0.0"]
# ... etc
all = [...]  # All optional deps
```

Removed (not needed for local-only):
- `requests` (was used for HTTP)
- `mcp` (MCP server)
- `uvicorn` / `starlette` (server)
- Azure SDKs
- YouTube transcript deps

## Checklist for Migration

1. ✅ Replace `markitdown` imports with `markdowner`
2. ✅ Remove URL/URI conversions
3. ✅ Add security limits if needed
4. ✅ Update exception handling for new exception types
5. ✅ Remove MCP/server code if used
6. ✅ Verify CLI workflows work (they should be compatible)

## Compatibility

For most CLI-based usage, MarkDowner is a drop-in replacement:

```bash
# This works the same
markitdown file.pdf
markdowner file.pdf

# This does NOT work in MarkDowner (by design)
markitdown https://...
```

## Support

If you encounter issues:
- Check that you're not using removed features
- Verify your input is a local file
- Ensure dependencies are installed for the formats you need
- Review SECURITY.md for limit configuration