# MarkDowner Security Review

## Executive Summary
**Verdict:** **FAIL (Not Production Ready)**

MarkDowner has made excellent progress descoping network risks and achieving its core functionality as a local CLI tool. The architectural shifts—removing the MCP server, HTTP fetching, and enforcing explicit size limits—are highly positive security enhancements. 

However, critical implementation flaws negate several of the intended security guardrails. Specifically, **input size limits and ZIP bomb protections can be trivially bypassed**, leading to Denial of Service (OOM crashes or infinite reads) when processing untrusted files. Additionally, systemic reliance on `stream.read()` without stream wrappers neutralizes the documented maximum size protections. 

Until the stream-handling constraints are strictly enforced dynamically during the read phase, the application cannot safely process untrusted user input in automated pipelines.

---

## Threat Model Snapshot

*   **Trust Boundaries:** The CLI interface and standard input (stdin) receive data from potentially untrusted origins.
*   **Attack Surface:** Parsing and conversion of complex, potentially malicious document formats (PDF, DOCX, ZIP, HTML, etc.).
*   **Primary Threats:**
    *   **Denial of Service (DoS):** Resource exhaustion via ZIP bombs, infinite streams (`/dev/zero`), or malformed structures triggering excessive memory allocation.
    *   **Execution / Injection:** Exploitation of underlying parser vulnerabilities (e.g., `pdfminer`, `mammoth`, `BeautifulSoup`, `ExifTool`).
    *   **Information Disclosure:** Path traversal during archive extraction or XXE (XML External Entity) attacks in underlying libraries.

---

## Findings Table

| Severity | Title | Evidence (File Path) | Impact | Exploitability | Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Critical** | **Zip Bomb Limit Bypass (Header Trust)** | `src/markdowner/converters/_zip_converter.py` (Line 59, 100) | Complete DoS (Memory Exhaustion) | High | Do not trust `info.file_size`. Read ZIP entries in chunks dynamically checking limits. |
| **Critical** | **Local File Limit Bypass & Infinite Read DoS** | `src/markdowner/_core.py` (Lines 185-188, 207) | Complete DoS (Memory Exhaustion) | High | Apply a bounded stream wrapper to local files instead of just relying on TOCTOU `os.path.getsize`. |
| **Medium** | **Temporary File Leak on OOM/Signal Kill** | Multiple converters (e.g., `_pdf_converter.py` Line 55) | Disk Exhaustion (Storage DoS) | Low | Use `tempfile.TemporaryDirectory()` with standard OS cleanup, or `delete=True` if OS allows. |
| **Low** | **Dormant `defusedxml` Dependency** | `pyproject.toml` (Line 23) | Missed XXE Protection | Low | Either implement XML defusing globally or remove the unused dependency to reduce supply chain surface. |

---

### Detailed Finding Analysis

#### 1. Zip Bomb Limit Bypass (Header Trust)
*   **Evidence:** In `_zip_converter.py`, the code verifies ZIP limits using `info.file_size` from the ZIP central directory: 
    `if not self._limits.check_zip_entry_size(info.file_size): ...`
    It then proceeds to read the entire file into memory simultaneously: 
    `content = zf.read(name)`
*   **Analysis:** The ZIP specification allows the `file_size` header to be arbitrarily defined. A malicious archive can declare `file_size = 10` but expand to 10GB of null bytes when decompressed. `zipfile.ZipFile.read()` will blindly decompress until the system runs out of memory.
*   **Fix:** Replace `zf.read(name)` with `with zf.open(name) as member:` and read in bounded chunks, incrementing a counter and raising `ZipLimitExceededException` if the dynamic count exceeds `max_zip_entry_bytes`.

#### 2. Local File Limit Bypass & Infinite Read DoS
*   **Evidence:** In `_core.py` (`convert_local`), file size is checked using `os.path.getsize(path_str)`. If it throws an `OSError` (e.g., a special device file like `/dev/zero`), the code explicitly bypasses the check: `pass # If we can't get size, skip check`. The raw file handle is then passed to converters which call `stream.read()`.
*   **Analysis:** This is a Time-of-Check to Time-of-Use (TOCTOU) vulnerability. More importantly, it permits endless reads from special files (`/dev/zero`, `/dev/urandom`) or named pipes, instantly causing an Out-Of-Memory crash when converters like `PlainTextConverter` call `.read()`.
*   **Fix:** Ensure that **all** inputs (including local files) are wrapped in a bounded stream reader (similar to `_coerce_stream_with_limit`) that dynamically enforces `max_input_bytes` during actual `.read()` operations.

#### 3. Temporary File Leak on OOM/Signal Kill
*   **Evidence:** Converters save streams to disk using `NamedTemporaryFile(delete=False)`, relying on a `finally: os.unlink(tmp_path)` block for cleanup.
*   **Analysis:** If the process is forcefully terminated (e.g., via SIGKILL due to the OOM vectors described above), the `finally` block will not execute. In an automated batch processing environment, this will eventually exhaust `/tmp` storage.
*   **Fix:** Refactor third-party integrations to accept file-like objects directly where possible. If physical paths are absolutely required, consider utilizing `tempfile.TemporaryDirectory` with context managers to encapsulate cleanup, though signal-based termination will still require OS-level `/tmp` lifecycle policies.

#### 4. Dormant `defusedxml` Dependency
*   **Evidence:** `pyproject.toml` declares `defusedxml>=0.7.0` in the base dependencies, but `rg defusedxml` would show it is never imported or utilized.
*   **Analysis:** MarkDowner relies on third-party libraries (`mammoth`, `python-pptx`, `ebooklib`) to parse XML-heavy formats. If `defusedxml` was added to mitigate XXE, it currently does nothing as it is not actively monkey-patching the standard library (a practice that was deprecated anyway) nor used explicitly. 
*   **Fix:** If you are relying on third-party libraries for XXE safety, remove `defusedxml` to reduce dependency bloat. If you intend to defuse standard library XML parsers, implement explicit usage or runtime patching.

---

## Security Control Verification Matrix

| Claimed Control | Verification Target | Status | Notes |
| :--- | :--- | :--- | :--- |
| **No HTTP fetching in core path** | `src/markdowner/_core.py` | **PASS** | Network fetch logic was successfully removed. |
| **No unauthenticated server mode** | Entire codebase | **PASS** | MCP and Uvicorn/Starlette logic removed. |
| **Max input bytes limit** | `_core.py` (`convert_local` & `convert_stream`) | **FAIL** | Stdin limits apply correctly, but local file limits rely on trusting OS metadata and bypass entirely on `OSError`. |
| **Max ZIP uncompressed limits** | `_zip_converter.py` | **FAIL** | ZIP limits rely on the easily forged `info.file_size` header instead of dynamic stream sizing. |
| **Max recursion depth** | `_zip_converter.py` | **PASS** | `_zip_depth` tracking is successfully propagated and enforced. |
| **ExifTool version guard** | `_image_converter.py` | **PASS** | The `_ensure_safe_exiftool` enforces `>=12.24` and caches results safely. |

---

## Test Coverage Gaps (Security-Focused)

To ensure regressions do not reintroduce these vulnerabilities, the following test cases must be added:

1.  **Forged ZIP Header Test (Zip Bomb):** Construct a ZIP file containing a highly compressed file (e.g., 100MB of null bytes) where the central directory `file_size` is manually hex-edited to report `10 bytes`. Validate that `ZipConverter` halts processing and raises an exception during decompression.
2.  **Special File DoS Test:** Attempt to convert `/dev/zero` using the local file pipeline. Assert that it raises `InputSizeExceededException` rather than hanging or exhausting memory.
3.  **Local File Symlink/TOCTOU Test:** Ensure that if a file grows between initialization and reading, the stream wrapper successfully terminates the read once `MAX_INPUT_BYTES` is crossed.

---

## Prioritized Remediation Plan

1.  **Phase 1: Stream Boundary Enforcement (Immediate)**
    *   Update `_core.py` to route local file handles (`fh`) through a dynamic chunk-reader wrapper that enforces `max_input_bytes` during the `.read()` phase, eliminating the reliance on `os.path.getsize`.
2.  **Phase 2: Secure Zip Extraction (Immediate)**
    *   Refactor `_zip_converter.py`. Remove `zf.read(name)`. Instead, use `with zf.open(name) as member:` and read the stream in 8KB chunks. Accumulate a `bytes_extracted` counter and raise an error immediately if it breaches `max_zip_entry_bytes`.
3.  **Phase 3: Housekeeping & Cleanup (Short Term)**
    *   Evaluate the necessity of `defusedxml` in `pyproject.toml`.
    *   Audit the `delete=False` temporary file patterns and replace them where underlying libraries natively support `.read()` streams instead of physical file paths.

---

## Codex CLI Security Review (Appended 2026-03-14)

**Findings**

- **Critical: local-file size limits are bypassable for special files and TOCTOU cases.** [`src/markdowner/_core.py:208`](/Users/max/Projects/MarkDowner/src/markdowner/_core.py#L208) checks `os.path.getsize()` once, skips enforcement on `OSError`, then hands the raw file handle to converters at [`src/markdowner/_core.py:239`](/Users/max/Projects/MarkDowner/src/markdowner/_core.py#L239). That means inputs like `/dev/zero`, FIFOs, procfs files, or files swapped after the size check can bypass the documented “input-size limit enforcement” claim in [`README.md:27`](/Users/max/Projects/MarkDowner/README.md#L27) and [`SECURITY.md:3`](/Users/max/Projects/MarkDowner/SECURITY.md#L3). Exploitation path: run `markdowner /dev/zero` or point automation at a named pipe; downstream code can read forever or until memory exhaustion. Remediation: wrap local file handles in the same bounded reader used for unseekable streams before any sniffing/conversion, and fail closed if file size cannot be determined or bounded.

- **Critical: ZIP bomb protections trust attacker-controlled headers and then fully decompress entries into memory.** [`src/markdowner/converters/_zip_converter.py:82`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_zip_converter.py#L82) and [`src/markdowner/converters/_zip_converter.py:109`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_zip_converter.py#L109) enforce limits using `ZipInfo.file_size`, then [`src/markdowner/converters/_zip_converter.py:122`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_zip_converter.py#L122) calls `zf.read(name)`, materializing the full decompressed payload. A forged archive can advertise small sizes while expanding far beyond limits. This contradicts the “ZIP entry limits” and “max uncompressed zip bytes” claims in [`README.md:33`](/Users/max/Projects/MarkDowner/README.md#L33) and [`SECURITY.md:20`](/Users/max/Projects/MarkDowner/SECURITY.md#L20). Exploitation path: submit a compressed bomb entry or nested bomb; `zf.read()` expands it in memory before any real byte-count enforcement. Remediation: replace `zf.read()` with `zf.open()` and stream entries in chunks, counting actual decompressed bytes and aborting once entry or cumulative totals exceed limits.

- **Medium: ZIP-based package detection is done outside the ZIP limit controls.** [`src/markdowner/converters/_zip_package_helpers.py:13`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_zip_package_helpers.py#L13) builds `set(zf.namelist())` with no entry-count or size guard. That helper is used by DOCX/PPTX/XLSX/EPUB acceptors, for example [`src/markdowner/converters/_docx_converter.py:33`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_docx_converter.py#L33) and [`src/markdowner/converters/_epub_converter.py:37`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_epub_converter.py#L37). Exploitation path: a crafted `.docx`/`.pptx`/`.xlsx`/`.epub` with an enormous central directory can force large metadata allocation before the safer ZIP converter is reached. Remediation: centralize ZIP inspection behind one bounded helper that enforces entry-count and metadata-size caps during format detection too.

- **Medium: optional format parsers are invoked without sandboxing or parser-specific resource limits.** The converters write attacker input to disk and hand it to heavy libraries directly: PDF [`src/markdowner/converters/_pdf_converter.py:60`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_pdf_converter.py#L60), DOCX [`src/markdowner/converters/_docx_converter.py:55`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_docx_converter.py#L55), PPTX [`src/markdowner/converters/_pptx_converter.py:55`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_pptx_converter.py#L55), XLSX [`src/markdowner/converters/_xlsx_converter.py:56`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_xlsx_converter.py#L56), EPUB [`src/markdowner/converters/_epub_converter.py:62`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_epub_converter.py#L62), MSG [`src/markdowner/converters/_outlook_msg_converter.py:59`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_outlook_msg_converter.py#L59). The repo claims “minimal attack surface” in [`src/markdowner/_core.py:48`](/Users/max/Projects/MarkDowner/src/markdowner/_core.py#L48), but there is no subprocess isolation, memory ceiling, or execution timeout around these parsers. Exploitation path: malicious but sub-100MB documents can trigger parser CPU or memory exhaustion in automation. Remediation: run risky parsers in isolated subprocesses with OS-level CPU/memory/time limits, and add per-format row/page/sheet/item caps before rendering to Markdown.

- **Low: temporary-file handling can leave sensitive content on disk after abnormal termination.** Multiple converters use `NamedTemporaryFile(..., delete=False)` and unlink only in normal `finally` blocks, e.g. PDF [`src/markdowner/converters/_pdf_converter.py:60`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_pdf_converter.py#L60), image [`src/markdowner/converters/_image_converter.py:120`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_image_converter.py#L120). Exploitation path: crash, `SIGKILL`, or host reboot leaves converted source material in temp storage. Remediation: use `TemporaryDirectory()` with restrictive permissions, keep temp lifetime scoped, and document temp-file hygiene for crash recovery.

- **Low: `defusedxml` is declared but unused, so any implied XML hardening is not real.** The dependency is present in [`pyproject.toml:27`](/Users/max/Projects/MarkDowner/pyproject.toml#L27), but there are no code imports or integrations. This is not a direct exploit by itself, but it is a documentation/control gap for XML-heavy formats. Remediation: either explicitly use hardened XML parsing where applicable or remove the dependency and stop implying XML hardening.

**Claimed vs Implemented Controls**

- `STATUS.md` is cited as the evidence source in [`SECURITY.md:11`](/Users/max/Projects/MarkDowner/SECURITY.md#L11) and [`README.md:49`](/Users/max/Projects/MarkDowner/README.md#L49), but that file is absent from the repository. The docs overstate verifiability.
- The docs claim verified input-size and ZIP-limit enforcement in [`SECURITY.md:3`](/Users/max/Projects/MarkDowner/SECURITY.md#L3), but the implementation only robustly enforces stdin/unseekable limits; local-file and real decompression limits are not enforced at read time.
- The ExifTool version gate is a real implemented control. [`src/markdowner/converters/_image_converter.py:32`](/Users/max/Projects/MarkDowner/src/markdowner/converters/_image_converter.py#L32) enforces `>= 12.24`, matching [`SECURITY.md:28`](/Users/max/Projects/MarkDowner/SECURITY.md#L28).

**Security Test Gaps**

- [`tests/test_security_limits.py:82`](/Users/max/Projects/MarkDowner/tests/test_security_limits.py#L82) mostly tests `Limits` boolean helpers, not adversarial decompression behavior. There is no regression test for forged ZIP header sizes or decompression-over-limit aborts.
- There is no test for the local-path bypass case (`/dev/zero`, FIFO, procfs, or TOCTOU swap). [`tests/test_security_limits.py:54`](/Users/max/Projects/MarkDowner/tests/test_security_limits.py#L54) only covers unseekable streams.
- Optional converters are not validated end-to-end in the reported environment. [`FINAL-IMPLEMENTATION-REPORT.md:14`](/Users/max/Projects/MarkDowner/FINAL-IMPLEMENTATION-REPORT.md#L14) and [`quality-report.md:29`](/Users/max/Projects/MarkDowner/quality-report.md#L29) explicitly say DOCX/PPTX/XLSX/EPUB/PDF dependencies were not installed, so those parser attack paths are effectively untested.
- There are no adversarial tests for parser complexity limits: huge worksheet counts, deeply nested XML/package structures, oversized metadata, malformed OLE streams, or hostile EPUB HTML.

**Production Readiness**

This is **not production-ready for untrusted input**. The ExifTool guard and some ZIP recursion controls are real, but the two critical DoS paths mean the repository does not currently satisfy its documented “security-first” posture for automated processing of attacker-supplied files.