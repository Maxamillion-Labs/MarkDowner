# Removals Document

This document lists all features removed from MarkItDown in the creation of MarkDowner, along with rationale.

## What Was Removed

### Network/URI Conversion

| Feature | Rationale |
|---------|------------|
| HTTP/HTTPS URI conversion | Eliminates SSRF attack surface |
| file:// URI conversion | Local file access via URI not needed |
| data:// URI conversion | Complex inline data not required |
| convert_url() method | Redundant with local-only design |
| convert_uri() method | Redundant with local-only design |
| convert_response() method | Not needed without network |

### Server/MCP Features

| Feature | Rationale |
|---------|------------|
| MCP server package | Eliminates unauthenticated server exposure |
| SSE endpoint | No streaming needed for local conversion |
| HTTP server mode | CLI-only design |
| uvicorn dependency | Only needed for server mode |
| starlette dependency | Only needed for server mode |

### Web-Specific Converters

| Feature | Rationale |
|---------|------------|
| YouTube converter | Requires network, removed |
| Wikipedia converter | Requires network, removed |
| Bing SERP converter | Requires network, removed |
| RSS converter | Requires network |

### Cloud/AI Features

| Feature | Rationale |
|---------|------------|
| Azure Document Intelligence | Requires cloud credentials, removed |
| LLM caption hooks | Requires external AI, disabled by default |
| Image caption via LLM | Requires external AI, disabled by default |
| Audio transcription via LLM | Requires external AI, disabled by default |

### Plugin System

| Feature | Rationale |
|---------|------------|
| Plugin auto-loading | Security risk - arbitrary code execution |
| Plugin entry points | Not needed for v1 |
| enable_plugins() method | Removed to eliminate attack surface |

### Dependencies Removed

| Dependency | Rationale |
|------------|-----------|
| requests | Only used for HTTP conversion |
| mcp | MCP server not included |
| azure-ai-form-recognizer | Azure Doc Intelligence |
| azure-identity | Azure Doc Intelligence |
| youtube-transcript-api | YouTube converter |
| pytube | YouTube converter |
| wikipedia | Wikipedia converter |
| beautifulsoup4 (kept) | Core HTML parsing needed |
| markdownify (kept) | Core markdown conversion needed |
| magika (kept) | File type detection needed |

## Code Removed

### From Core

- URI parsing in convert() method
- HTTP/HTTPS handling
- Response conversion
- Plugin loading mechanism

### From Converters

- `_youtube_converter.py` - Removed
- `_wikipedia_converter.py` - Removed
- `_bing_serp_converter.py` - Removed
- `_doc_intel_converter.py` - Removed
- `_rss_converter.py` - Removed
- `_llm_caption.py` - Removed (LLM hooks)
- `_transcribe_audio.py` - Removed (network-based)

### From Dependencies

All network-related and server-related packages removed from pyproject.toml

## Migration Impact

For users migrating from MarkItDown:

1. **CLI workflows remain the same** - File-based conversion works identically
2. **URL conversion not available** - Use curl/wget to download first, then convert
3. **Server mode not available** - Use CLI or script directly
4. **Security limits added** - May need adjustment for large files

## Rationale Summary

The removals follow a "secure by default" philosophy:

1. **Attack surface reduction** - Every feature removed is potential attack surface
2. **Simplicity** - Less code means fewer bugs
3. **Local-first** - Designed for local file conversion, not web scraping
4. **Security boundaries** - Clear separation between trusted and untrusted input