# Security Notes

## Verified Limit Enforcement

### Command
```bash
python3 -m pytest tests/test_security_limits.py -v
```

### Output
Not captured separately. See `STATUS.md` final `python3 -m pytest tests/ -v` output for these passing checks:

```text
tests/test_security_limits.py::TestInputSizeLimits::test_input_size_exception_for_unseekable_stream PASSED [ 73%]
tests/test_security_limits.py::TestZipLimits::test_zip_too_many_entries_raises_exception PASSED [ 82%]
tests/test_security_limits.py::TestRecursionLimits::test_nested_zip_recursion_limit PASSED [ 86%]
tests/test_security_limits.py::TestLimitsFactory::test_create_custom_limits_preserves_zero_values PASSED [ 91%]
```

## Current Defaults

- `max_input_bytes = 100 * 1024 * 1024`
- `max_zip_entries = 1000`
- `max_zip_total_uncompressed_bytes = 200 * 1024 * 1024`
- `max_zip_entry_bytes = 50 * 1024 * 1024`
- `max_recursion_depth = 3`

## Image Metadata Guard

- ExifTool version check requires `>= 12.24`
- Invalid version output, missing binary, and vulnerable versions are covered by tests in `tests/test_conversion_parity.py`
