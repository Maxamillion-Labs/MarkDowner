# Baseline

## Pre-fix Baseline Commands

### Command
```bash
python3 -m pytest tests/ -q
```

### Output
```text
..........................                                        [100%]
33 passed in 2.07s
```

### Command
```bash
python3 -m markdowner --version
```

### Output
```text
markdowner 1.0.0
```

## Fixture Corpus

- `tests/test_files/sample.txt`
- `tests/test_files/sample.html`
- `tests/test_files/sample.csv`
- `tests/test_files/sample.zip`
- `tests/test_files/sample.docx`
- `tests/test_files/sample.xlsx`
- `tests/test_files/sample.pdf`

## Post-fix Fixture Validation

### Command
```bash
python3 -m pytest tests/test_fixture_corpus.py -v
```

### Output
Not captured separately. See `STATUS.md` final `python3 -m pytest tests/ -v` output, which includes:

```text
tests/test_fixture_corpus.py::test_fixture_directory_is_populated PASSED [ 57%]
tests/test_fixture_corpus.py::test_text_html_csv_and_zip_fixtures_convert PASSED [ 60%]
tests/test_fixture_corpus.py::test_docx_xlsx_and_pdf_fixtures_match_signature_checks PASSED [ 62%]
```
