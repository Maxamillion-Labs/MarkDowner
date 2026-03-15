# MarkDowner Unified Fix Plan (Agent Execution Runbook)

Date: 2026-03-14  
Applies to: `~/Projects/MarkDowner`  
Goal: Resolve all issues identified in Gemini + Codex reviews and bring project to production-ready quality.

---

## 0) Execution Rules (Read First)

1. Work in order. Do **not** skip phases.
2. Keep changes minimal and targeted to each step.
3. After each phase:
   - run tests,
   - update `STATUS.md` with factual results,
   - commit checkpoint.
4. No fabricated claims in docs. Everything must be verifiable by tests/artifacts.
5. If blocked, document blocker + workaround in `STATUS.md`, then continue.

---

## 1) Branch + Baseline

### Step 1.1 — Create fix branch
- Create branch: `fix/review-remediation-v1`

### Step 1.2 — Record baseline (before changes)
Run and capture outputs:
- `python3 -m pytest tests/ -q`
- `python3 -m markdowner --version`
- `python3 -m markdowner --help`

Write results to `STATUS.md` under **Baseline (pre-fix)**.

**Exit criteria**
- Baseline command outputs captured in `STATUS.md`.

---

## 2) Phase A — Critical Correctness + Security (Blockers)

## Step 2.1 — Enforce input-size limits incrementally (no full pre-buffer)

**Files**
- `src/markdowner/__main__.py`
- `src/markdowner/_core.py`

**Actions**
1. Implement chunked read helper for stdin/unseekable streams.
2. Track cumulative bytes during read.
3. Raise `InputSizeExceededException` immediately when limit exceeded.
4. Reuse same helper in all relevant ingestion paths.

**Tests**
- Add/upgrade tests for oversized stdin and oversized unseekable stream.

**Exit criteria**
- Oversized piped input fails fast without full buffering behavior.

---

## Step 2.2 — Fix ZIP conversion routing + deterministic ordering

**Files**
- `src/markdowner/converters/_zip_converter.py`
- `src/markdowner/_core.py` (if needed for depth propagation)

**Actions**
1. For each ZIP entry, pass content to `self._markdowner.convert_stream(...)` (not `ZipConverter.convert()` recursion on all files).
2. Sort entry names before processing for deterministic order.
3. Enforce zip limits (entry count, entry bytes, total bytes, recursion depth).
4. Return structured warnings/metadata for skipped or failed entries.

**Tests**
- Strengthen ZIP test to assert **inner content extraction**, not just filename.
- Add mixed-entry ZIP test (supported + unsupported) and warning assertions.
- Add nested ZIP depth-limit test.

**Exit criteria**
- ZIP content extraction works for non-archive inner files.
- Ordering deterministic and test-verified.

---

## Step 2.3 — Add ExifTool version guard (>= 12.24)

**Files**
- `src/markdowner/converters/_image_converter.py`
- optional helper module for ExifTool checks

**Actions**
1. Run `exiftool -ver`, parse version.
2. Enforce minimum `12.24` before metadata extraction.
3. Cache successful version check for process lifetime.
4. If missing/invalid/vulnerable, skip metadata extraction with explicit warning.

**Tests**
- Mock subprocess for valid, invalid, missing-binary, and vulnerable-version cases.

**Exit criteria**
- Version guard enforced and test-covered.

---

## Step 2.4 — Restore HTML to real Markdown conversion

**Files**
- `src/markdowner/converters/_html_converter.py`

**Actions**
1. Use `markdownify` pipeline instead of plain `get_text()`.
2. Strip script/style safely.
3. Preserve structure (headings, links, lists, tables as feasible).

**Tests**
- Add HTML fixture/assertions for headings, links, list markers.

**Exit criteria**
- HTML output retains markdown structure, not plain text dump.

---

## 3) Phase B — Reliability Contract + Converter Hardening

## Step 3.1 — Fix failure semantics (no false success)

**Files**
- `src/markdowner/_core.py`
- `src/markdowner/__main__.py`
- converter modules returning empty success on exception

**Actions**
1. Define conversion result contract:
   - fatal conversion failures should not be reported as successful empty output.
2. Ensure CLI prints warnings to `stderr`.
3. Return non-zero exit code on conversion failure.
4. Keep best-effort behavior explicit where intended.

**Tests**
- Add malformed input tests expecting non-zero exit.

**Exit criteria**
- Broken documents do not silently pass as success.

---

## Step 3.2 — Tighten format detection for ZIP-based formats

**Files**
- `src/markdowner/converters/_docx_converter.py`
- `src/markdowner/converters/_pptx_converter.py`
- `src/markdowner/converters/_xlsx_converter.py`
- `src/markdowner/converters/_epub_converter.py`

**Actions**
1. Remove broad “magic PK only” acceptance where it causes false positives.
2. Require stronger extension/mimetype/package-signature checks.
3. Fix EPUB implementation correctness (library usage/import paths).

**Tests**
- Add negative tests to confirm plain ZIP is not misclassified.

**Exit criteria**
- Converter selection is deterministic and correct.

---

## Step 3.3 — Refactor CSV conversion path for encoding stability

**Files**
- `src/markdowner/converters/_csv_converter.py`

**Actions**
1. Prefer stream/BytesIO-based read path.
2. Explicit encoding handling/fallback with warnings.
3. Remove unnecessary temporary-file + implicit encoding pitfalls.

**Tests**
- Add utf-8 and cp1252 sample tests.

**Exit criteria**
- CSV conversion stable across common encodings.

---

## Step 3.4 — Replace silent exception swallowing with observable warnings

**Files**
- `src/markdowner/converters/_epub_converter.py`
- `src/markdowner/converters/_outlook_msg_converter.py`
- any `except Exception: pass` paths

**Actions**
1. Convert silent catches into warning entries in `DocumentConverterResult.warnings`.
2. Keep sensitive paths redacted where needed.

**Exit criteria**
- No critical silent exception swallowing remains.

---

## 4) Phase C — Tests, Fixtures, and Evidence

## Step 4.1 — Build real fixture corpus

**Files/Dirs**
- `tests/test_files/`
- `BASELINE.md`

**Actions**
1. Add minimal real fixtures: txt/html/csv/zip/docx/xlsx/pdf (small safe fixtures).
2. Add baseline snapshot expectations where appropriate.

**Exit criteria**
- `tests/test_files/` is non-empty and used by tests.

---

## Step 4.2 — Expand coverage to required formats and behaviors

**Files**
- `tests/test_conversion_parity.py`
- new `tests/test_zip_behavior.py`
- `tests/test_cli_parity.py`
- `tests/test_security_limits.py`

**Actions**
1. Add format tests for in-scope types (at least smoke-level for optional converters).
2. Add MIME/charset hint validation tests.
3. Strengthen assertions to validate output content quality.

**Exit criteria**
- Tests fail when key regressions are reintroduced (ZIP, HTML, limits).

---

## Step 4.3 — Validate CI matrix and packaging truth

**Files**
- `.github/workflows/ci.yml`
- `pyproject.toml`

**Actions**
1. Align Python requirement with spec (`>=3.10` unless intentionally changed and documented).
2. Ensure CI runs target matrix and passes.

**Exit criteria**
- Local tests pass and CI config is consistent with packaging metadata.

---

## 5) Phase D — Documentation Integrity (No overclaims)

## Step 5.1 — Correct docs to match verified reality

**Files**
- `STATUS.md`
- `quality-report.md`
- `BASELINE.md`
- `SECURITY.md`
- `MIGRATION.md`
- `README.md`

**Actions**
1. Remove any unverifiable claims.
2. Add “Verified by command” sections with exact command outputs.
3. Fix API example mismatches and stale references.
4. Add missing `LICENSE` file (if still missing and claimed by docs).

**Exit criteria**
- Every claim in docs maps to artifact/test/command output.

---

## 6) Final Validation Gate (Must pass all)

Run:

```bash
cd ~/Projects/MarkDowner
python3 -m markdowner --version
python3 -m markdowner --help
python3 -m pytest tests/ -v
```

Also manually verify required workflows:

```bash
python3 -m markdowner sample.txt
python3 -m markdowner sample.txt -o out.md
cat sample.txt | python3 -m markdowner -x .txt
python3 -m markdowner -x .txt < sample.txt
```

### Release-ready criteria
- All tests pass.
- Required CLI workflows pass.
- Priority A blockers fully resolved.
- Docs reflect evidence only.

If any Priority A item fails => **NOT READY**.

---

## 7) Commit Plan (required)

1. `fix: enforce streaming input limits + tests`
2. `fix: correct zip routing/order + tests`
3. `fix: exiftool version guard + tests`
4. `fix: html markdown conversion`
5. `fix: converter failure semantics + cli exit codes`
6. `fix: format detection + epub/csv hardening`
7. `test: add fixture corpus and stronger assertions`
8. `docs: reconcile status/quality/security/readme with verified results`

---

## 8) Expected Deliverables after execution

- Code fixes across core/converters for all critical issues.
- Expanded test suite with real fixtures and stronger assertions.
- Accurate docs and status artifacts.
- Clean final `STATUS.md` with command outputs and pass/fail evidence.
