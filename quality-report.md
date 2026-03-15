# Quality Report

## Local Test Result

### Command
```bash
python3 -m pytest tests/ -q
```

### Output
```text
......................................                            [100%]
45 passed in 2.06s
```

## Behaviors Covered by Tests

- CLI file/stdin/output workflows
- Oversized stdin rejection
- Malformed ZIP non-zero exit behavior
- HTML Markdown structure
- ZIP deterministic ordering and nested archive routing
- ExifTool version guard warning paths
- CSV encoding fallback handling
- Limit factory zero-value preservation
- Plain ZIP rejection by DOCX/PPTX/XLSX/EPUB detectors
- Fixture corpus presence and smoke coverage

## Local Environment Constraint

### Command
```bash
python3 - <<'PY'
mods = ['pandas','openpyxl','mammoth','pptx','ebooklib','pdfplumber']
for mod in mods:
    try:
        __import__(mod)
        print(mod, 'yes')
    except Exception as exc:
        print(mod, 'no', type(exc).__name__)
PY
```

### Output
```text
pandas yes
openpyxl no ModuleNotFoundError
mammoth no ModuleNotFoundError
pptx no ModuleNotFoundError
ebooklib no ModuleNotFoundError
pdfplumber no ModuleNotFoundError
```
