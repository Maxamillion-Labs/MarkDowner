# CHANGELOG.md

## Overview — What Changed from the Microsoft MarkItDown Baseline

MarkDowner started from a MarkItDown-style foundation and was intentionally evolved into a **local-only, reliability-first, security-hardened** conversion engine for automation and AI workflows.

Key directional changes:
- Shifted to a stricter **local trust boundary** (no built-in remote fetch pipeline in core flow).
- Added stronger **defensive controls** around input handling, archives, parser isolation, and fallback behavior.
- Added/expanded **native RTF conversion path** and hardened parsing behavior.
- Expanded **Outlook MSG attachment handling** to support practical automation use while staying safe and non-fatal on failures.

---

## Security Hardening Highlights

### 1) Input and local-source protections
- Enforced read-time input-size controls.
- Rejects unsafe/non-regular local sources.
- Hardened local open/stat behavior to reduce unsafe path/race patterns.

### 2) Archive (ZIP) safety limits
- Enforces entry-count limits.
- Enforces per-entry decompressed byte limits.
- Enforces total decompressed byte limits.
- Enforces recursion-depth limits.
- Uses bounded handling for archive-based format detection/routing.

### 3) Parser isolation and resilience
- Parser subprocess limits for timeout/memory.
- Improved sandbox IPC handling to avoid deadlock on larger payload returns.
- Better controlled error propagation for parser worker failures.

### 4) Fallback policy hardening
- Narrowed conversion fallback semantics so failures don’t silently degrade into unsafe/incorrect generic output.
- Added explicit recoverable-failure signaling path.
- Supports strict-mode behavior to disable fallback in high-assurance contexts.

### 5) Temp-file hygiene
- Scoped temporary file/materialization behavior with cleanup guarantees in normal and failure paths.

---

## RTF-Related Improvements

RTF support was expanded and hardened as part of this fork’s core mission:
- Dedicated native RTF conversion path.
- Improved parser behavior and test coverage around RTF lexical/parsing edge cases.
- Better reliability for common RTF structures used in business/automation docs.

Security relevance:
- Reduced dependency on external conversion binaries for RTF path.
- More deterministic parser behavior and controlled failure handling.

---

## Outlook MSG + Attachment Handling Improvements

MSG conversion now includes practical attachment-aware behavior:
- Converts main email body to markdown.
- Extracts attachment payloads where available.
- Routes supported attachments through normal converter pipeline.
- Writes deterministic sibling attachment markdown outputs when using `-o`.
- Treats unsupported/failed attachment conversion as **non-fatal** and reports concise warnings.
- Detects unsupported embedded Outlook item attachments and warns clearly.

Security/reliability relevance:
- Maintains conversion continuity for main message.
- Avoids hard-fail cascades from single bad/unsupported attachment.
- Improved subprocess/result handling for large attachment payload scenarios.

---

## Documentation and Operability Updates

- README repositioned around local-only, secure, automation/AI usage.
- Spec and user guide updated to reflect as-built behavior.
- Added cross-platform installation guide (macOS/Linux/Windows).
- CI checks expanded for fixture presence and optional dependency paths.

---

## Validation Snapshot

Latest local full suite result:

```bash
.venv/bin/python -m pytest -q
```

Result:
- **145 passed**
