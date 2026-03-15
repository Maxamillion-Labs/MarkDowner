# MarkDowner Specification

## 1. Purpose

**MarkDowner** is a stripped-down, CLI-first fork of Microsoft MarkItDown focused on one job:

> Convert local files and stdin streams into Markdown reliably, with minimal attack surface and no server/runtime extras.

This spec defines scope, architecture, feature set, constraints, implementation phases, and acceptance criteria.

---

## 2. Product Goals

1. **Keep core conversion power** across major file types.
2. **Preserve familiar CLI ergonomics**:
   - `markdowner input.pdf`
   - `markdowner input.pdf -o output.md`
   - `cat input.pdf | markdowner -x .pdf`
   - `markdowner < input.pdf -x .pdf`
3. **Eliminate unnecessary complexity** (MCP/server mode, network fetch paths, cloud extras by default).
4. **Improve reliability and safety** for local automation use.

---

## 3. Non-Goals

MarkDowner will **not** include:

- MCP server (`markitdown-mcp`) support
- SSE/HTTP serving modes
- Remote URI conversion by default (`http://`, `https://`, `data:`, `file:` URI parsing paths)
- Azure Document Intelligence integration (default fork state)
- Web-specific converters requiring remote fetch logic (YouTube/Wikipedia/Bing SERP)
- “Do-everything” plugin marketplace behavior in v1

---

## 4. Scope (v1)

### 4.1 In-scope conversions (local file + stdin)

- PDF
- DOCX
- PPTX
- XLSX
- XLS
- HTML/HTM (local content only)
- CSV
- JSON
- XML
- Plain text
- EPUB
- Outlook MSG
- Images (JPG/JPEG/PNG)
- Audio (WAV/MP3/M4A/MP4)
- ZIP (recursive conversion of supported contained files)

### 4.2 CLI behavior to preserve

- Input from file path argument
- Input from stdin binary stream
- Output to stdout by default
- Output to file via `-o/--output`
- Extension hint for stdin via `-x/--extension`
- MIME hint via `-m/--mime-type`
- Charset hint via `-c/--charset`
- Version output

---

## 5. Project Structure

Target folder:

- `projects/MarkDowner/`

Recommended package structure:

```text
MarkDowner/
  README.md
  LICENSE
  pyproject.toml
  src/markdowner/
    __init__.py
    __main__.py
    core.py
    stream_info.py
    exceptions.py
    converters/
      ...
  tests/
    test_cli_*.py
    test_module_*.py
    test_files/
```

Notes:
- Keep a **single package** for v1 simplicity.
- Do not include MCP package or server scaffolding.

---

## 6. Architecture

### 6.1 Core components

1. **CLI layer (`__main__.py`)**
   - Parse arguments
   - Build conversion context
   - Route input source (path or stdin)
   - Emit result to stdout or output file

2. **Conversion orchestrator (`core.py`)**
   - Register converters
   - Infer stream metadata (extension/mimetype/charset)
   - Try converters by priority
   - Return normalized Markdown

3. **Converter interface (`base converter`)**
   - `accepts(stream, stream_info, **kwargs) -> bool`
   - `convert(stream, stream_info, **kwargs) -> Result`

4. **Per-format converters**
   - One module per format family

### 6.2 Processing model

- No network call path in core orchestrator
- Stream-first operation where possible
- Controlled buffering when required by third-party libs
- Deterministic converter ordering by explicit priority

---

## 7. Dependency Strategy

### 7.1 Python version

- `>=3.10`

### 7.2 Base dependencies (minimal always-on)

- `beautifulsoup4`
- `markdownify`
- `magika`
- `charset-normalizer`
- `defusedxml`

### 7.3 Optional feature groups

- `[pdf]` -> `pdfminer.six`, `pdfplumber`
- `[docx]` -> `mammoth`, `lxml`
- `[pptx]` -> `python-pptx`
- `[xlsx]` -> `pandas`, `openpyxl`
- `[xls]` -> `pandas`, `xlrd`
- `[outlook]` -> `olefile`
- `[audio]` -> `pydub`, `SpeechRecognition`
- `[all]` -> all local conversion groups

### 7.4 Removed dependencies

- `mcp`
- `uvicorn` / `starlette` (if only present for MCP package)
- Azure Document Intelligence SDK deps in v1 default
- YouTube transcript deps if network converters removed

---

## 8. Security Requirements

### 8.1 Hard requirements

1. **No HTTP fetching in core path** (v1)
2. **No unauthenticated server mode** (MCP removed)
3. **No implicit plugin execution** in v1
4. **Bounds on untrusted input**:
   - max input bytes (configurable)
   - max zip entries
   - max uncompressed zip bytes
   - max per-entry bytes
   - max recursion depth for nested archives

### 8.2 Safe defaults

- Plugins disabled / absent
- Network disabled
- Fail closed on unsupported formats
- Clear warnings for partial conversion

### 8.3 Third-party tool safety

- Preserve ExifTool version guard (`>=12.24`) before use
- Graceful fallback when optional tools unavailable

---

## 9. Reliability Requirements

1. **No silent data loss where avoidable**
   - ZIP converter must report skipped files in result metadata/warnings
2. **Deterministic output normalization**
   - consistent line endings and whitespace normalization
3. **Resource-aware behavior**
   - avoid unbounded buffering where practical
4. **Stable CLI exit semantics**
   - `0` success
   - non-zero for conversion failure / invalid args

---

## 10. Usability Requirements

1. Preserve straightforward CLI commands.
2. Keep errors human-readable and actionable.
3. Include `--help` examples for common workflows.
4. Maintain output compatibility with shell pipelines.

---

## 11. CLI Specification

Command name:

- Primary: `markdowner`

Arguments:

- `markdowner [filename]`
- `-o, --output <path>`: write Markdown to file
- `-x, --extension <.ext>`: hint extension for stdin
- `-m, --mime-type <type/subtype>`
- `-c, --charset <encoding>`
- `--version`
- `--help`

Behavior:

- If `filename` omitted: read `sys.stdin.buffer`
- If output omitted: print to stdout using safe encoding fallback
- Validate MIME/charset hints early

---

## 12. Converter Coverage Matrix (v1)

| Format | Support | Notes |
|---|---|---|
| PDF | Yes | text/table extraction; fallback path retained |
| DOCX | Yes | mammoth-based HTML-to-Markdown pipeline |
| PPTX | Yes | shape/text/image metadata support |
| XLSX/XLS | Yes | tabular sheet conversion |
| HTML | Yes | local HTML only |
| CSV/JSON/XML/TXT | Yes | structured text conversion |
| EPUB | Yes | local conversion |
| MSG | Yes | metadata/body extraction |
| Images | Yes | metadata + optional LLM caption hooks disabled by default |
| Audio | Yes | metadata + optional transcription |
| ZIP | Yes | recursive local conversion with limits |
| URL input | No (v1) | intentionally removed |
| MCP transport | No | intentionally removed |

---

## 13. Testing Specification

### 13.1 Unit tests

- Converter acceptance routing
- Stream metadata inference
- CLI argument parsing and error handling
- Output normalization

### 13.2 Integration tests

- Golden-file comparison using fixture corpus
- stdin + `-x` conversion scenarios
- zip recursion + limits
- large-file guardrail behavior

### 13.3 Compatibility tests

- Compare selected MarkItDown outputs vs MarkDowner outputs on same fixtures
- Define acceptable deltas (formatting differences tolerated, content loss not tolerated)

### 13.4 CI matrix

- Python 3.10, 3.11, 3.12, 3.13
- Lint + tests on push/PR

---

## 14. Migration Plan from MarkItDown

### Phase 0: Bootstrap
- Copy MarkItDown core converter package into `MarkDowner`.
- Rename package/module references to `markdowner`.

### Phase 1: De-scope
- Remove MCP package entirely.
- Remove URL/URI conversion pathways from orchestrator.
- Remove cloud and web converters (Doc Intel, YouTube, Wikipedia, Bing).

### Phase 2: Harden
- Add file/zip size and recursion limits.
- Add timeout wrappers where feasible.
- Convert silent skips to explicit warnings.

### Phase 3: Polish
- Finalize CLI docs and examples.
- Align dependency extras and packaging metadata.
- Run regression and fixture tests.

---

## 15. Acceptance Criteria (v1)

MarkDowner v1 is complete when all are true:

1. CLI supports file path, `-o`, and stdin piping workflows exactly as specified.
2. All in-scope local file formats convert successfully with fixture tests passing.
3. No MCP/server code remains.
4. No HTTP/HTTPS/data/file URI conversion path remains by default.
5. Zip and input guardrails are implemented and tested.
6. CI passes across Python 3.10–3.13.
7. Documentation clearly states scope, limits, and examples.

---

## 16. Risks and Mitigations

1. **Behavior drift from upstream**
   - Mitigation: keep fixture-based compatibility tests.
2. **Dependency churn in document libs**
   - Mitigation: pin minimum tested versions and regular update cadence.
3. **Performance regressions on large docs**
   - Mitigation: benchmark representative corpus; enforce limits.
4. **Silent conversion gaps**
   - Mitigation: structured warning/report output in result metadata.

---

## 17. Future Extensions (post-v1, optional)

- Optional plugin support behind explicit trust flag
- Structured JSON report mode (`--report`) for automation pipelines
- Parallel conversion mode for batch jobs

---

## 18. Implementation Notes from MarkItDown Audit

This spec is informed by observed MarkItDown code characteristics:

- Good converter abstraction and prioritization model (worth preserving)
- Useful format breadth (worth preserving)
- MCP package introduces unnecessary exposure for this use case (remove)
- Some paths currently buffer entire streams and silently skip failures (improve)

---

## 19. Versioning and Naming

- Project name: **MarkDowner**
- CLI command: **markdowner**
- Initial version: `0.1.0` (internal MVP) or `1.0.0` if release-ready

---

## 20. Decision Log (Initial)

1. CLI-first local converter product
2. No MCP/server mode in v1
3. No network URI conversion in v1
4. Keep broad local file format conversion support
5. Prioritize reliability and safety guardrails over feature breadth
