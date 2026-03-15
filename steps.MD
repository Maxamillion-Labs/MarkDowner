# MarkDowner Security Remediation Punchlist

Date: 2026-03-14  
Sources combined: Gemini security review + Codex CLI security review (`fix.MD`)

## Scope
This punchlist is the exact implementation plan to remediate all security findings raised by both reviews.

---

## Execution Rules

1. Complete items in priority order (**P0 → P1 → P2**).
2. Each item must include:
   - code change,
   - tests,
   - docs update,
   - verification output recorded in `STATUS.md`.
3. No “fixed” claim unless the corresponding tests exist and pass.

---

## P0 (Blockers — must complete before untrusted-input use)

## P0-1: Enforce hard input limits for local files and special files

**Issue addressed**
- Local-file size check bypass (`os.path.getsize` TOCTOU / special files like `/dev/zero`)
- Infinite-read DoS risk

**Files**
- `src/markdowner/_core.py`
- (new) `src/markdowner/_bounded_stream.py` (recommended)
- `tests/test_security_limits.py`
- `tests/test_cli_parity.py`

**Implementation steps**
1. Add a bounded stream wrapper class that enforces `max_input_bytes` during `read()` calls (not pre-check only).
2. In `convert_local`, always wrap opened file handles with this bounded wrapper before converter routing.
3. If source is non-regular file (device, FIFO, procfs), either:
   - reject by default with explicit error, or
   - allow only if bounded wrapper is active and limit-enforced.
4. Remove/replace any `except OSError: pass` that skips size protection.

**Tests to add**
- `test_local_special_file_is_blocked_or_bounded` (simulate /dev-like stream via monkeypatch)
- `test_local_file_growth_toctou_still_stops_at_limit`
- `test_cli_rejects_infinite_like_input` (safe mock, no real hang)

**Done when**
- Local path conversion cannot bypass size limits.
- Security tests prove bounded behavior on read-time, not metadata-only checks.

---

## P0-2: Replace ZIP header-trust logic with streaming decompression enforcement

**Issue addressed**
- ZIP bomb bypass via forged `ZipInfo.file_size`
- Full in-memory `zf.read(name)` decompression risk

**Files**
- `src/markdowner/converters/_zip_converter.py`
- `tests/test_security_limits.py`
- `tests/test_zip_behavior.py`

**Implementation steps**
1. Replace `zf.read(name)` with `zf.open(name)` and read in chunks (e.g., 8192 bytes).
2. Track **actual decompressed bytes** per entry and total archive bytes while streaming.
3. Abort immediately with `ZipLimitExceededException` when crossing:
   - `max_zip_entry_bytes`
   - `max_zip_total_uncompressed_bytes`
4. Keep recursion-depth checks; ensure nested archive limits are enforced at stream time too.
5. Keep deterministic ordering and metadata/warning propagation intact.

**Tests to add**
- `test_zip_streaming_enforces_entry_limit_on_actual_bytes`
- `test_zip_streaming_enforces_total_limit_on_actual_bytes`
- `test_nested_zip_bomb_stops_with_limit_exception`

**Done when**
- ZIP limits are enforced on actual extracted bytes, not header metadata.

---

## P0-3: Bound ZIP package detection helper (DOCX/PPTX/XLSX/EPUB acceptors)

**Issue addressed**
- `zip_has_members` currently scans ZIP metadata outside limit controls

**Files**
- `src/markdowner/converters/_zip_package_helpers.py`
- `src/markdowner/converters/_docx_converter.py`
- `src/markdowner/converters/_pptx_converter.py`
- `src/markdowner/converters/_xlsx_converter.py`
- `src/markdowner/converters/_epub_converter.py`
- `tests/test_zip_behavior.py`

**Implementation steps**
1. Extend helper to accept bounds (entry count and metadata scan cap).
2. Avoid full `set(zf.namelist())`; iterate lazily and short-circuit when required members found.
3. If ZIP metadata exceeds safe threshold, fail detection safely (return false + optional warning path).
4. Ensure acceptors call bounded helper consistently.

**Tests to add**
- `test_zip_member_scan_has_hard_entry_cap`
- `test_acceptors_do_not_scan_unbounded_zip_metadata`

**Done when**
- Format detection cannot trigger unbounded ZIP metadata work.

---

## P1 (High value hardening)

## P1-1: Add parser isolation/timeouts for heavy converters

**Issue addressed**
- Risky third-party parsers run in-process with no per-parser resource control

**Files**
- (new) `src/markdowner/_sandbox.py`
- Converter files: `_pdf_converter.py`, `_docx_converter.py`, `_pptx_converter.py`, `_xlsx_converter.py`, `_epub_converter.py`, `_outlook_msg_converter.py`
- `tests/test_security_limits.py` (or new `tests/test_parser_sandbox.py`)

**Implementation steps**
1. Execute heavy parser work in subprocess worker with:
   - timeout (wall clock)
   - memory cap (where platform supports)
2. Return controlled failure when timeout/memory limit hit.
3. Preserve current converter outputs/warnings contract.

**Tests to add**
- `test_parser_timeout_returns_controlled_failure`
- `test_parser_worker_failure_does_not_crash_main_process`

**Done when**
- Malicious parser workload can’t hang or OOM the main process silently.

---

## P1-2: Harden temporary-file lifecycle

**Issue addressed**
- Temp files may remain on disk on abrupt process kill

**Files**
- `_pdf_converter.py`, `_docx_converter.py`, `_pptx_converter.py`, `_xlsx_converter.py`, `_epub_converter.py`, `_outlook_msg_converter.py`, `_image_converter.py`
- `SECURITY.md`

**Implementation steps**
1. Use `TemporaryDirectory()` wrappers per conversion operation.
2. Ensure restrictive permissions for temp directories/files.
3. Document crash-residual behavior and cleanup policy.

**Tests to add**
- `test_temp_paths_scoped_and_cleaned_on_normal_exit`

**Done when**
- Temp artifacts are minimized and behavior is documented accurately.

---

## P2 (Control alignment, test completeness, documentation integrity)

## P2-1: Resolve `defusedxml` mismatch

**Issue addressed**
- Dependency declared but not used; implied control unclear

**Files**
- `pyproject.toml`
- relevant XML handling code/docs

**Implementation steps (choose one path)**
- **Path A:** integrate `defusedxml` where XML parsing occurs and add tests.
- **Path B (recommended if no XML parser is used):** remove dependency and remove any implied XML-hardening claims.

**Done when**
- Dependency list and documented controls match actual implementation.

---

## P2-2: Add adversarial security regression tests

**Issue addressed**
- Current tests miss key attack paths

**Files**
- `tests/test_security_limits.py`
- new `tests/test_security_regressions.py`

**Required new tests**
1. forged ZIP metadata vs real decompressed bytes
2. local special-file/infinite-stream path
3. TOCTOU-like growth behavior
4. parser timeout failure path
5. nested archive complexity stress within limits

**Done when**
- Reintroducing any P0 bug causes deterministic test failure.

---

## P2-3: Fix documentation/evidence alignment

**Issue addressed**
- Security claims overstate verifiability in places

**Files**
- `README.md`
- `SECURITY.md`
- `STATUS.md`
- `FINAL-IMPLEMENTATION-REPORT.md`
- `quality-report.md`

**Implementation steps**
1. Ensure every security claim references a passing test or exact command output.
2. Add explicit “current residual risks” section.
3. If any control is partial, label it partial (not pass).

**Done when**
- No unverifiable or overstated security claims remain.

---

## Suggested Commit Sequence

1. `fix(security): enforce bounded local-file reads and special-file handling`
2. `fix(security): stream zip extraction with real-byte limit enforcement`
3. `fix(security): bound zip package signature scanning`
4. `feat(security): parser subprocess isolation with timeout/memory limits`
5. `fix(security): temp file lifecycle hardening`
6. `test(security): add adversarial regression coverage`
7. `docs(security): align claims with verified controls and residual risks`

---

## Final Verification Gate

Run and record outputs:

```bash
cd ~/Projects/MarkDowner
python3 -m pytest tests/ -v
python3 -m markdowner --help
python3 -m markdowner --version
```

Plus targeted security suite:

```bash
python3 -m pytest tests/test_security_limits.py -v
python3 -m pytest tests/test_zip_behavior.py -v
python3 -m pytest tests/test_security_regressions.py -v
```

### Ship Criteria
- All P0 items complete and test-covered.
- No critical findings remain in rerun security review.
- Docs match implementation and tests exactly.

If any P0 item is incomplete: **Not ready for untrusted input production use.**
