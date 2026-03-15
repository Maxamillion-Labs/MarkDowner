# Security Notes

## Verified Controls

- Local-file conversion enforces `max_input_bytes` during `read()` calls and rejects non-regular local sources.
- ZIP conversion streams entries with chunked decompression and aborts on actual-byte entry and total limits.
- ZIP-based package detection uses bounded metadata scans instead of `set(zf.namelist())`.
- Heavy parser entry points run in subprocess workers with timeout handling and best-effort address-space limits.
- Temp materialization uses `TemporaryDirectory()` with private directory/file permissions and normal-exit cleanup coverage.

## Verified Commands

- `python3 -m pytest tests/test_security_limits.py -v`
- `python3 -m pytest tests/test_zip_behavior.py -v`
- `python3 -m pytest tests/test_security_regressions.py -v`

## Current Defaults

- `max_input_bytes = 100 * 1024 * 1024`
- `max_zip_entries = 1000`
- `max_zip_total_uncompressed_bytes = 200 * 1024 * 1024`
- `max_zip_entry_bytes = 50 * 1024 * 1024`
- `max_recursion_depth = 3`
- `max_zip_metadata_entries = 2048`
- `max_zip_metadata_scan_bytes = 524288`

## Residual Risks

- End-to-end execution of DOCX, PPTX, XLSX, EPUB, PDF, and MSG converters was not verified in this environment because their optional runtime packages are not all installed.
- Temp cleanup on abrupt interpreter termination or `SIGKILL` cannot be guaranteed; only normal-exit cleanup is covered.
- Subprocess memory caps rely on `resource.RLIMIT_AS` support and degrade to timeout-only isolation where the platform does not honor that limit.
