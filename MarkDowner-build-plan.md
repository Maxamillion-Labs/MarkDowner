# MarkDowner Build Plan

Version: 1.0  
Date: 2026-03-14  
Project: `~/Projects/MarkDowner`  
Base source: `~/Projects/markitdown`

---

## 1) Objective

Build **MarkDowner** as a stripped-down, CLI-first, local-only document-to-Markdown converter derived from MarkItDown.

### Success definition (top-level)

MarkDowner is successful when all are true:

1. CLI workflows work exactly:
   - `markdowner input.pdf`
   - `markdowner input.pdf -o output.md`
   - `cat input.pdf | markdowner -x .pdf`
   - `markdowner < input.pdf -x .pdf`
2. No MCP/server/runtime HTTP surfaces exist in codebase.
3. No network fetch path exists in default conversion flow.
4. In-scope local file types convert with passing tests.
5. Security guardrails (size/depth/zip limits) are implemented and tested.
6. CI passes on Python 3.10–3.13.

---

## 2) Scope Summary

### In scope (v1)
- Local file + stdin conversion only
- File types: PDF, DOCX, PPTX, XLSX/XLS, HTML, CSV/JSON/XML/TXT, EPUB, MSG, images, audio, ZIP
- CLI parity with MarkItDown core usage

### Out of scope (v1)
- MCP package and HTTP/SSE server
- URI conversion (`http`, `https`, `data`, `file`) in core flow
- Azure Doc Intelligence mode
- YouTube/Wikipedia/Bing converters
- Plugin marketplace behavior by default

---

## 3) Phase Plan (with measurable outcomes)

## Phase 0 — Project Bootstrap & Baseline Capture

### Goal
Create a clean project baseline and capture current behavior to avoid regressions.

### Tasks
- [ ] Create Python package scaffold for `markdowner`
- [ ] Copy baseline fixture corpus from MarkItDown tests into `MarkDowner/tests/test_files`
- [ ] Capture baseline outputs from upstream MarkItDown for representative files
- [ ] Create issue tracker labels: `phase-0..phase-5`, `security`, `parity`, `docs`

### Deliverables
- `pyproject.toml` (MarkDowner)
- `src/markdowner/*` scaffold
- `tests/fixtures-baseline/` markdown snapshots
- `BASELINE.md`

### Measurable outcomes
- ✅ At least **20 fixture files** have baseline markdown snapshots.
- ✅ `python -m markdowner --help` returns 0.
- ✅ CI skeleton exists and runs lint job.

### Exit gate
Phase ends when baseline data is committed and reproducible.

---

## Phase 1 — CLI/Core Parity (Local + Stdin)

### Goal
Implement core conversion orchestration and preserve required CLI behavior.

### Tasks
- [ ] Implement CLI args:
  - `filename?`, `-o/--output`, `-x/--extension`, `-m/--mime-type`, `-c/--charset`, `--version`
- [ ] Implement path input and stdin binary input handling
- [ ] Implement output to stdout/file
- [ ] Implement converter registration and priority ordering
- [ ] Implement stream info inference (extension/mimetype/charset)

### Deliverables
- `src/markdowner/__main__.py`
- `src/markdowner/core.py`
- `src/markdowner/stream_info.py`

### Measurable outcomes
- ✅ 4 required CLI workflows pass in integration tests.
- ✅ CLI exit code behavior documented and tested.
- ✅ Output normalization deterministic (line ending tests pass).

### Exit gate
`tests/test_cli_parity.py` passes 100%.

---

## Phase 2 — De-scope/Strip Down

### Goal
Remove all non-essential and network/server features.

### Tasks
- [ ] Remove MCP/server code from MarkDowner codebase
- [ ] Remove URI conversion path from core (`http/https/data/file`)
- [ ] Remove web-specific converters (YouTube/Wikipedia/Bing)
- [ ] Remove Azure Doc Intelligence converter and flags
- [ ] Remove plugin auto-load path (or hard-disable in v1)
- [ ] Prune dependencies to local-only set

### Deliverables
- `REMOVALS.md` (what was removed + rationale)
- Updated `pyproject.toml` with local-only extras

### Measurable outcomes
- ✅ `rg -n "uvicorn|starlette|mcp|convert_uri|youtube|wikipedia|docintel" src/` returns **0 intended runtime references**.
- ✅ No CLI options reference removed features.
- ✅ Dependency graph no longer includes MCP/server libs.

### Exit gate
Static grep checks + test suite green.

---

## Phase 3 — Security Hardening

### Goal
Add defensive controls for untrusted files/archives.

### Tasks
- [ ] Add global limits config:
  - `MAX_INPUT_BYTES`
  - `MAX_ZIP_ENTRIES`
  - `MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES`
  - `MAX_ZIP_ENTRY_BYTES`
  - `MAX_RECURSION_DEPTH`
- [ ] Enforce limits in stdin/file ingestion path
- [ ] Add zip bomb protections and recursion guards
- [ ] Replace silent skips with structured warnings
- [ ] Keep ExifTool CVE minimum version guard

### Deliverables
- `src/markdowner/limits.py`
- `src/markdowner/security.py`
- `SECURITY.md` (MarkDowner-specific)

### Measurable outcomes
- ✅ Tests for oversized input fail safely with clear error messages.
- ✅ Tests for oversized ZIP / too many entries fail safely.
- ✅ No unbounded zip extraction behavior remains.
- ✅ 0 silent exception-swallowing in critical conversion loops (except explicitly documented non-fatal paths).

### Exit gate
`tests/test_security_limits.py` all green.

---

## Phase 4 — Reliability & Conversion Quality

### Goal
Stabilize conversions and preserve content fidelity while improving observability.

### Tasks
- [ ] Implement conversion report metadata (warnings/errors/skipped files)
- [ ] Ensure converter failures are observable in report/log output
- [ ] Add compatibility tests against baseline snapshots
- [ ] Add deterministic ordering for ZIP converted entries
- [ ] Validate large-file behavior under limits

### Deliverables
- `tests/test_conversion_parity.py`
- `tests/test_zip_behavior.py`
- `docs/quality-report.md`

### Measurable outcomes
- ✅ At least **90% fixture parity** with baseline for text-content equivalence.
- ✅ **0 hard crashes** on malformed sample files in fixture suite.
- ✅ ZIP conversion report includes skipped file names and reasons.

### Exit gate
Quality report committed + parity threshold achieved.

---

## Phase 5 — Packaging, CI, and Release Readiness

### Goal
Make MarkDowner easy to install, test, and release.

### Tasks
- [ ] Finalize package metadata and console entrypoint `markdowner`
- [ ] Add CI matrix for 3.10/3.11/3.12/3.13
- [ ] Add lint, type checks (optional), tests, and build checks
- [ ] Write docs:
  - `README.md`
  - `MIGRATION.md` (from MarkItDown)
  - `USAGE.md`
- [ ] Create release checklist and version tag plan

### Deliverables
- GitHub Actions workflows
- release notes template
- `v0.1.0` (or `v1.0.0`) candidate

### Measurable outcomes
- ✅ CI green across all target Python versions.
- ✅ `pip install -e .` + `markdowner --version` works on clean env.
- ✅ README includes all required CLI examples.

### Exit gate
Release candidate passes install + smoke tests on fresh environment.

---

## 4) Work Breakdown Structure (WBS)

- **WBS-1 Core Package**
  - WBS-1.1 package scaffold
  - WBS-1.2 CLI parser
  - WBS-1.3 converter orchestrator
- **WBS-2 Converter Set**
  - WBS-2.1 local text/table formats
  - WBS-2.2 office formats
  - WBS-2.3 media formats
  - WBS-2.4 zip recursion
- **WBS-3 De-scope**
  - WBS-3.1 remove MCP/server
  - WBS-3.2 remove network/URI path
  - WBS-3.3 remove cloud/web converters
- **WBS-4 Security**
  - WBS-4.1 limits
  - WBS-4.2 error surfacing
  - WBS-4.3 regression tests for malicious/large inputs
- **WBS-5 Quality + Release**
  - WBS-5.1 parity tests
  - WBS-5.2 CI matrix
  - WBS-5.3 docs and release

---

## 5) Measurable KPI Dashboard

Track weekly:

1. **Feature completeness**: `% phase checklist done`
2. **Test health**: pass rate by module
3. **Parity score**: fixture text-equivalence percent
4. **Security coverage**: number of guardrail tests passing
5. **Crash-free malformed files**: count / total malformed corpus
6. **Performance smoke**: median conversion time by file type class

Target thresholds before release:
- Parity score ≥ 90%
- Security test pass rate = 100%
- CI matrix pass rate = 100%
- Crash-free malformed corpus = 100%

---

## 6) Test Matrix (minimum)

### CLI tests
- [ ] file input -> stdout
- [ ] file input -> `-o`
- [ ] stdin + `-x`
- [ ] bad MIME/charset hints error cleanly

### Format tests
- [ ] PDF
- [ ] DOCX
- [ ] PPTX
- [ ] XLSX/XLS
- [ ] HTML
- [ ] CSV/JSON/XML/TXT
- [ ] EPUB
- [ ] MSG
- [ ] image
- [ ] audio
- [ ] zip

### Security tests
- [ ] oversized stdin
- [ ] oversized local file
- [ ] zip with too many entries
- [ ] zip with oversized entry
- [ ] zip nested depth exceeded

---

## 7) Risks and Mitigations

1. **Upstream drift from MarkItDown**
   - Mitigation: maintain frozen baseline fixtures and periodic sync review.
2. **Third-party parser instability**
   - Mitigation: strict version ranges + malformed file tests.
3. **Scope creep (plugins/network returning too early)**
   - Mitigation: enforce v1 out-of-scope policy.
4. **Performance degradation after guardrails**
   - Mitigation: benchmark before/after and tune limits.

---

## 8) Definition of Done (project-level)

Project is done when:

- [ ] All phase exit gates passed
- [ ] KPI thresholds met
- [ ] Security and migration docs complete
- [ ] Release candidate tagged
- [ ] Install + smoke test verified on fresh environment

---

## 9) Suggested Immediate Next Actions

1. Create `src/markdowner/` scaffold and wire CLI entrypoint.
2. Copy core local converters from MarkItDown.
3. Remove MCP/network/cloud/web paths first (Phase 2 early).
4. Add limit constants and zip guardrails immediately after parity baseline.
5. Build parity/security tests before optimization.

---

## 10) Change Control

Any new capability request must state:

- Why it is needed
- Whether it introduces network/server surface
- Security impact
- Test coverage added
- Which phase gate it affects

If it increases attack surface, it is deferred beyond v1 unless explicitly approved.
