# Migration Notes

## Import Change

```python
from markdowner import MarkDowner

md = MarkDowner()
result = md.convert("document.pdf")
```

## Removed Scope

- No URL conversion path
- No server mode
- No plugin auto-loading

## Verified CLI Compatibility

### Command
```bash
python3 -m markdowner sample.txt
```

### Output
```text
Sample text for CLI validation.
```

### Command
```bash
cat sample.txt | python3 -m markdowner -x .txt
```

### Output
```text
Sample text for CLI validation.
```
