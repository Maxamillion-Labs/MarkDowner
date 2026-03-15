# Status Log

## Commit Status

### Previous blocker
A prior sub-agent run reported an `index.lock` permission issue while attempting checkpoint commits.

### Current status
Commit permissions are now working in this environment; remediation changes are being committed from this branch.

## P0-1: Enforce hard input limits for local files and special files

### Command
```bash
python3 -m pytest tests/test_security_limits.py -v
```

### Output
```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/max/Projects/MarkDowner
configfile: pyproject.toml
collecting ... collected 18 items

tests/test_security_limits.py::TestInputSizeLimits::test_default_limit_allows_normal_input PASSED [  5%]
tests/test_security_limits.py::TestInputSizeLimits::test_default_limit_blocks_oversized_input PASSED [ 11%]
tests/test_security_limits.py::TestInputSizeLimits::test_limits_disabled_allows_any_size PASSED [ 16%]
tests/test_security_limits.py::TestInputSizeLimits::test_input_size_exception_raised PASSED [ 22%]
tests/test_security_limits.py::TestInputSizeLimits::test_input_size_exception_for_unseekable_stream PASSED [ 27%]
tests/test_security_limits.py::TestInputSizeLimits::test_local_special_file_is_blocked_or_bounded PASSED [ 33%]
tests/test_security_limits.py::TestInputSizeLimits::test_local_file_growth_toctou_still_stops_at_limit PASSED [ 38%]
tests/test_security_limits.py::TestZipLimits::test_zip_entry_count_limit PASSED [ 44%]
tests/test_security_limits.py::TestZipLimits::test_zip_total_size_limit PASSED [ 50%]
tests/test_security_limits.py::TestZipLimits::test_zip_entry_size_limit PASSED [ 55%]
tests/test_security_limits.py::TestZipLimits::test_zip_too_many_entries_raises_exception PASSED [ 61%]
tests/test_security_limits.py::TestZipLimits::test_zip_streaming_enforces_entry_limit_on_actual_bytes PASSED [ 66%]
tests/test_security_limits.py::TestZipLimits::test_zip_streaming_enforces_total_limit_on_actual_bytes PASSED [ 72%]
tests/test_security_limits.py::TestZipLimits::test_nested_zip_bomb_stops_with_limit_exception PASSED [ 77%]
tests/test_security_limits.py::TestRecursionLimits::test_recursion_depth_limit PASSED [ 83%]
tests/test_security_limits.py::TestRecursionLimits::test_nested_zip_recursion_limit PASSED [ 88%]
tests/test_security_limits.py::TestLimitsFactory::test_create_custom_limits PASSED [ 94%]
tests/test_security_limits.py::TestLimitsFactory::test_create_custom_limits_preserves_zero_values PASSED [100%]

============================== 18 passed in 0.24s ==============================
```

### Command
```bash
python3 -m pytest tests/test_cli_parity.py -v
```

### Output
```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/max/Projects/MarkDowner
configfile: pyproject.toml
collecting ... collected 11 items

tests/test_cli_parity.py::test_cli_file_to_stdout PASSED                 [  9%]
tests/test_cli_parity.py::test_cli_file_to_output_file PASSED            [ 18%]
tests/test_cli_parity.py::test_cli_stdin_with_extension PASSED           [ 27%]
tests/test_cli_parity.py::test_cli_stdin_redirect_with_extension PASSED  [ 36%]
tests/test_cli_parity.py::test_cli_version PASSED                        [ 45%]
tests/test_cli_parity.py::test_cli_help PASSED                           [ 54%]
tests/test_cli_parity.py::test_cli_missing_file PASSED                   [ 63%]
tests/test_cli_parity.py::test_cli_empty_stdin PASSED                    [ 72%]
tests/test_cli_parity.py::test_cli_oversized_stdin_fails_fast PASSED     [ 81%]
tests/test_cli_parity.py::test_cli_malformed_zip_returns_non_zero PASSED [ 90%]
tests/test_cli_parity.py::test_cli_rejects_infinite_like_input PASSED    [100%]

============================== 11 passed in 1.84s ==============================
```

## P0-2 and P0-3: ZIP streaming enforcement and bounded ZIP package detection

### Command
```bash
python3 -m pytest tests/test_zip_behavior.py -v
```

### Output
```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/max/Projects/MarkDowner
configfile: pyproject.toml
collecting ... collected 6 items

tests/test_zip_behavior.py::test_plain_zip_is_not_misclassified_as_docx PASSED [ 16%]
tests/test_zip_behavior.py::test_plain_zip_is_not_misclassified_as_pptx PASSED [ 33%]
tests/test_zip_behavior.py::test_plain_zip_is_not_misclassified_as_xlsx PASSED [ 50%]
tests/test_zip_behavior.py::test_plain_zip_is_not_misclassified_as_epub PASSED [ 66%]
tests/test_zip_behavior.py::test_zip_member_scan_has_hard_entry_cap PASSED [ 83%]
tests/test_zip_behavior.py::test_acceptors_do_not_scan_unbounded_zip_metadata PASSED [100%]

============================== 6 passed in 0.12s ===============================
```

## P1 and P2: Parser isolation, temp lifecycle hardening, regression coverage, and documentation alignment

### Command
```bash
python3 -m pytest tests/test_security_regressions.py -v
```

### Output
```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/max/Projects/MarkDowner
configfile: pyproject.toml
collecting ... collected 7 items

tests/test_security_regressions.py::test_forged_zip_metadata_vs_real_decompressed_bytes PASSED [ 14%]
tests/test_security_regressions.py::test_local_special_file_infinite_stream_path PASSED [ 28%]
tests/test_security_regressions.py::test_toctou_like_growth_behavior PASSED [ 42%]
tests/test_security_regressions.py::test_parser_timeout_returns_controlled_failure PASSED [ 57%]
tests/test_security_regressions.py::test_parser_worker_failure_does_not_crash_main_process PASSED [ 71%]
tests/test_security_regressions.py::test_temp_paths_scoped_and_cleaned_on_normal_exit PASSED [ 85%]
tests/test_security_regressions.py::test_nested_archive_complexity_stress_within_limits PASSED [100%]

============================== 7 passed in 1.32s ==============================
```

## Final Verification Gate

### Command
```bash
python3 -m pytest tests/ -v
```

### Output
```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/max/Projects/MarkDowner
configfile: pyproject.toml
collecting ... collected 60 items

tests/test_cli_parity.py::test_cli_file_to_stdout PASSED                 [  1%]
tests/test_cli_parity.py::test_cli_file_to_output_file PASSED            [  3%]
tests/test_cli_parity.py::test_cli_stdin_with_extension PASSED           [  5%]
tests/test_cli_parity.py::test_cli_stdin_redirect_with_extension PASSED  [  6%]
tests/test_cli_parity.py::test_cli_version PASSED                        [  8%]
tests/test_cli_parity.py::test_cli_help PASSED                           [ 10%]
tests/test_cli_parity.py::test_cli_missing_file PASSED                   [ 11%]
tests/test_cli_parity.py::test_cli_empty_stdin PASSED                    [ 13%]
tests/test_cli_parity.py::test_cli_oversized_stdin_fails_fast PASSED     [ 15%]
tests/test_cli_parity.py::test_cli_malformed_zip_returns_non_zero PASSED [ 16%]
tests/test_cli_parity.py::test_cli_rejects_infinite_like_input PASSED    [ 18%]
tests/test_conversion_parity.py::TestPlainTextConversion::test_convert_simple_text PASSED [ 20%]
tests/test_conversion_parity.py::TestPlainTextConversion::test_convert_text_file PASSED [ 21%]
tests/test_conversion_parity.py::TestHtmlConversion::test_convert_simple_html PASSED [ 23%]
tests/test_conversion_parity.py::TestZipConversion::test_convert_simple_zip PASSED [ 25%]
tests/test_conversion_parity.py::TestZipConversion::test_zip_conversion_is_deterministic_and_warns_for_unsupported_entries PASSED [ 26%]
tests/test_conversion_parity.py::TestZipConversion::test_zip_nested_text_content_is_extracted PASSED [ 28%]
tests/test_conversion_parity.py::TestImageConversion::test_exiftool_valid_version_extracts_metadata PASSED [ 30%]
tests/test_conversion_parity.py::TestImageConversion::test_exiftool_invalid_version_output_warns PASSED [ 31%]
tests/test_conversion_parity.py::TestImageConversion::test_exiftool_missing_binary_warns PASSED [ 33%]
tests/test_conversion_parity.py::TestImageConversion::test_exiftool_vulnerable_version_warns PASSED [ 35%]
tests/test_conversion_parity.py::TestCsvConversion::test_convert_simple_csv PASSED [ 36%]
tests/test_conversion_parity.py::TestCsvConversion::test_convert_utf8_csv_with_charset_hint PASSED [ 38%]
tests/test_conversion_parity.py::TestCsvConversion::test_convert_cp1252_csv_with_fallback_warning PASSED [ 40%]
tests/test_conversion_parity.py::TestExtensionInference::test_extension_from_path PASSED [ 41%]
tests/test_conversion_parity.py::TestMimetypeHints::test_mimetype_hint PASSED [ 43%]
tests/test_fixture_corpus.py::test_fixture_directory_is_populated PASSED [ 45%]
tests/test_fixture_corpus.py::test_text_html_csv_and_zip_fixtures_convert PASSED [ 46%]
tests/test_fixture_corpus.py::test_docx_xlsx_and_pdf_fixtures_match_signature_checks PASSED [ 48%]
tests/test_security_limits.py::TestInputSizeLimits::test_default_limit_allows_normal_input PASSED [ 50%]
tests/test_security_limits.py::TestInputSizeLimits::test_default_limit_blocks_oversized_input PASSED [ 51%]
tests/test_security_limits.py::TestInputSizeLimits::test_limits_disabled_allows_any_size PASSED [ 53%]
tests/test_security_limits.py::TestInputSizeLimits::test_input_size_exception_raised PASSED [ 55%]
tests/test_security_limits.py::TestInputSizeLimits::test_input_size_exception_for_unseekable_stream PASSED [ 56%]
tests/test_security_limits.py::TestInputSizeLimits::test_local_special_file_is_blocked_or_bounded PASSED [ 58%]
tests/test_security_limits.py::TestInputSizeLimits::test_local_file_growth_toctou_still_stops_at_limit PASSED [ 60%]
tests/test_security_limits.py::TestZipLimits::test_zip_entry_count_limit PASSED [ 61%]
tests/test_security_limits.py::TestZipLimits::test_zip_total_size_limit PASSED [ 63%]
tests/test_security_limits.py::TestZipLimits::test_zip_entry_size_limit PASSED [ 65%]
tests/test_security_limits.py::TestZipLimits::test_zip_too_many_entries_raises_exception PASSED [ 66%]
tests/test_security_limits.py::TestZipLimits::test_zip_streaming_enforces_entry_limit_on_actual_bytes PASSED [ 68%]
tests/test_security_limits.py::TestZipLimits::test_zip_streaming_enforces_total_limit_on_actual_bytes PASSED [ 70%]
tests/test_security_limits.py::TestZipLimits::test_nested_zip_bomb_stops_with_limit_exception PASSED [ 71%]
tests/test_security_limits.py::TestRecursionLimits::test_recursion_depth_limit PASSED [ 73%]
tests/test_security_limits.py::TestRecursionLimits::test_nested_zip_recursion_limit PASSED [ 75%]
tests/test_security_limits.py::TestLimitsFactory::test_create_custom_limits PASSED [ 76%]
tests/test_security_limits.py::TestLimitsFactory::test_create_custom_limits_preserves_zero_values PASSED [ 78%]
tests/test_security_regressions.py::test_forged_zip_metadata_vs_real_decompressed_bytes PASSED [ 80%]
tests/test_security_regressions.py::test_local_special_file_infinite_stream_path PASSED [ 81%]
tests/test_security_regressions.py::test_toctou_like_growth_behavior PASSED [ 83%]
tests/test_security_regressions.py::test_parser_timeout_returns_controlled_failure PASSED [ 85%]
tests/test_security_regressions.py::test_parser_worker_failure_does_not_crash_main_process PASSED [ 86%]
tests/test_security_regressions.py::test_temp_paths_scoped_and_cleaned_on_normal_exit PASSED [ 88%]
tests/test_security_regressions.py::test_nested_archive_complexity_stress_within_limits PASSED [ 90%]
tests/test_zip_behavior.py::test_plain_zip_is_not_misclassified_as_docx PASSED [ 91%]
tests/test_zip_behavior.py::test_plain_zip_is_not_misclassified_as_pptx PASSED [ 93%]
tests/test_zip_behavior.py::test_plain_zip_is_not_misclassified_as_xlsx PASSED [ 95%]
tests/test_zip_behavior.py::test_plain_zip_is_not_misclassified_as_epub PASSED [ 96%]
tests/test_zip_behavior.py::test_zip_member_scan_has_hard_entry_cap PASSED [ 98%]
tests/test_zip_behavior.py::test_acceptors_do_not_scan_unbounded_zip_metadata PASSED [100%]

============================== 60 passed in 3.33s ==============================
```

### Command
```bash
python3 -m markdowner --help
```

### Output
```text
usage: markdowner [-h] [-o OUTPUT] [-x EXTENSION] [-m MIME_TYPE] [-c CHARSET]
                  [--version]
                  [filename]

Convert local files and stdin to Markdown

positional arguments:
  filename              Input file path (omit for stdin)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file path (default: stdout)
  -x EXTENSION, --extension EXTENSION
                        File extension hint for stdin (e.g., .pdf, .docx)
  -m MIME_TYPE, --mime-type MIME_TYPE
                        MIME type hint for stdin (e.g., application/pdf)
  -c CHARSET, --charset CHARSET
                        Character encoding hint (e.g., utf-8)
  --version             show program's version number and exit

Examples:
  markdowner input.pdf                    Convert file to stdout
  markdowner input.pdf -o output.md       Convert file to output file
  cat input.pdf | markdowner -x .pdf      Convert stdin with extension hint
  markdowner < input.pdf -x .pdf          Convert stdin with redirect
        
```

### Command
```bash
python3 -m markdowner --version
```

### Output
```text
markdowner 1.0.0
```
