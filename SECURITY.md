# Security Documentation

## Overview

MarkDowner is designed with security as a core principle. It removes network functionality and implements multiple layers of protection against malicious files.

## Security Features

### 1. No Network Access

MarkDowner has **no network capabilities**:
- No HTTP/HTTPS conversion
- No file:// URI parsing
- No data:// URI parsing
- No MCP server mode
- No plugin auto-loading

This eliminates entire classes of attacks:
- SSRF via URL conversion
- Server-side request forgery
- Remote code execution via plugins

### 2. Input Size Limits

All input is subject to configurable size limits:

| Limit | Default | Configurable |
|-------|---------|---------------|
| Max input bytes | 100 MB | ✅ |
| Max ZIP entries | 1,000 | ✅ |
| Max ZIP uncompressed | 200 MB | ✅ |
| Max ZIP entry size | 50 MB | ✅ |

These prevent:
- Memory exhaustion attacks
- Disk space exhaustion
- ZIP bomb attacks
- Nested archive attacks

### 3. Recursion Depth Limits

Nested archives are limited to 3 levels by default:

```python
from markdowner import create_custom_limits

limits = create_custom_limits(max_recursion_depth=2)
```

### 4. Safe Parsing

- Uses `defusedxml` for XML parsing
- HTML sanitization via BeautifulSoup
- Charset detection with safe fallbacks

### 5. ExifTool Version Guard

If ExifTool is used for image metadata:
- Requires version >= 12.24 (CVE-protected)
- Falls back gracefully if unavailable

## Configuration

### Default Limits

```python
from markdowner import MarkDowner
from markdowner._limits import Limits

# Uses defaults
md = MarkDowner()
```

### Custom Limits

```python
from markdowner import MarkDowner
from markdowner._limits import create_custom_limits

limits = create_custom_limits(
    max_input_bytes=50 * 1024 * 1024,  # 50 MB
    max_zip_entries=500,
    max_zip_total_uncompressed_bytes=100 * 1024 * 1024,  # 100 MB
    max_zip_entry_bytes=25 * 1024 * 1024,  # 25 MB
    max_recursion_depth=2,
)

md = MarkDowner(limits=limits)
```

### Disable Limits

```python
from markdowner import MarkDowner
from markdowner._limits import create_custom_limits

# Disable all limits (NOT RECOMMENDED for untrusted input)
limits = create_custom_limits(enabled=False)
md = MarkDowner(limits=limits)
```

## Threat Model

### What MarkDowner Protects Against

1. **Large file DoS** - Input size limits prevent memory exhaustion
2. **ZIP bombs** - Entry count and size limits prevent decompression bombs
3. **Nested archive attacks** - Recursion limits prevent deep nesting
4. **Network-based attacks** - No network capability eliminates SSRF, etc.
5. **Plugin injection** - No plugin auto-loading prevents malicious code execution

### What MarkDowner Does NOT Protect Against

1. **Malicious file content** - If a supported file format contains malicious content (e.g., a PDF with embedded malware), MarkDowner will still extract text from it. This is expected behavior for a document converter.
2. **Denial of service via complex files** - Very complex but small files may cause excessive processing time. Consider adding timeouts for such cases.
3. **Exploits in third-party libraries** - MarkDowner uses third-party libraries (pdfminer, mammoth, etc.). Keep these updated.

## Best Practices

### For Untrusted Input

1. **Always use limits**

```python
md = MarkDowner()  # Uses default limits
```

2. **Lower limits for untrusted sources**

```python
limits = create_custom_limits(
    max_input_bytes=10 * 1024 * 1024,  # 10 MB max
    max_zip_entries=100,
)
md = MarkDowner(limits=limits)
```

3. **Consider timeouts**

```python
import signal
import sys

def timeout_handler(signum, frame):
    print("Conversion timeout", file=sys.stderr)
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout
```

### For Trusted Input

If you trust the input completely, you can disable limits:

```python
limits = create_custom_limits(enabled=False)
md = MarkDowner(limits=limits)
```

**Warning**: Only do this for truly trusted input!

## Reporting Security Issues

If you discover a security vulnerability in MarkDowner, please report it responsibly. Check the repository for security contact information.

## Changelog

### v1.0.0
- Initial release
- No network access by default
- Configurable input limits
- ZIP entry/size limits
- Recursion depth limits