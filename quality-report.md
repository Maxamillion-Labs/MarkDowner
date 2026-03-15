# Quality Report

## Local Test Result

### Command
```bash
python3 -m pytest tests/ -v
```

### Output
```text
See `STATUS.md` for the full 60-test output captured from:

- `python3 -m pytest tests/ -v`
- `python3 -m pytest tests/test_security_limits.py -v`
- `python3 -m pytest tests/test_zip_behavior.py -v`
- `python3 -m pytest tests/test_security_regressions.py -v`
```

## Behaviors Covered by Tests

- CLI file/stdin/output workflows
- Oversized stdin rejection
- Malformed ZIP non-zero exit behavior
- HTML Markdown structure
- ZIP deterministic ordering, nested archive routing, and actual-byte limit enforcement
- ExifTool version guard warning paths
- CSV encoding fallback handling
- Parser sandbox timeout and worker-failure paths
- TemporaryDirectory cleanup and restrictive permissions
- Limit factory zero-value preservation
- Plain ZIP rejection plus bounded DOCX/PPTX/XLSX/EPUB package detection
- Fixture corpus presence and smoke coverage

## Local Environment Note

Project-local `.venv` now includes optional converter dependencies used by the security remediation run.
Validation was executed in `.venv` with `python -m pytest tests/ -q` and passed (`60 passed`).
