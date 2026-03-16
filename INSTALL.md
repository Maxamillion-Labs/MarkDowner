# MarkDowner Installation Guide (macOS, Linux, Windows)

This guide covers installing and running MarkDowner on all major desktop/server platforms.

---

## 1) Prerequisites

- Python **3.10+**
- `pip`
- Git (recommended)

Check versions:

```bash
python --version
pip --version
```

> On some systems, use `python3`/`pip3` instead.

---

## 2) Get the project

```bash
git clone <YOUR-REPO-URL> MarkDowner
cd MarkDowner
```

If you already have the repo locally, just `cd` into it.

---

## 3) Create and activate virtual environment

## macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Windows (cmd.exe)

```cmd
py -3 -m venv .venv
.venv\Scripts\activate.bat
```

---

## 4) Install MarkDowner

### Base install

```bash
pip install -U pip
pip install -e .
```

### Install with all optional converters

```bash
pip install -e ".[all]"
```

### If you only need specific converters

```bash
pip install -e ".[pdf,docx,xlsx,xls,pptx,epub,outlook]"
```

---

## 5) Optional system tool: ExifTool (image metadata)

MarkDowner can run without this, but image metadata extraction is better with ExifTool.

## macOS (Homebrew)

```bash
brew install exiftool
```

## Linux

### Debian/Ubuntu
```bash
sudo apt-get update
sudo apt-get install -y libimage-exiftool-perl
```

### Fedora/RHEL
```bash
sudo dnf install -y perl-Image-ExifTool
```

## Windows

- Install ExifTool from the official distribution and ensure it is on `PATH`.
- Verify:

```powershell
exiftool -ver
```

---

## 6) Verify installation

```bash
python -m markdowner --version
```

Quick conversion test:

```bash
python -m markdowner tests/test_files/sample.txt
```

Run full test suite:

```bash
python -m pytest -q
```

---

## 7) First-use examples

Convert file to stdout:

```bash
python -m markdowner input.pdf
```

Convert file to output markdown file:

```bash
python -m markdowner input.docx -o output.md
```

Convert from stdin with extension hint:

```bash
cat input.rtf | python -m markdowner -x .rtf > output.md
```

---

## 8) Platform-specific notes

## macOS
- If using Homebrew Python, `python3` is usually the correct interpreter.
- If shell says command not found after venv activation, open a new shell and reactivate.

## Linux
- Some distros separate `python3-venv`; install it if `venv` creation fails.
- Example (Debian/Ubuntu):
  ```bash
  sudo apt-get install -y python3-venv
  ```

## Windows
- If PowerShell blocks activation scripts:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Then reactivate the venv.

---

## 9) Troubleshooting

### `python: command not found`
Use `python3` (macOS/Linux) or `py -3` (Windows).

### Dependency-related converter failures
Install needed extras (for example `.[pdf]`, `.[docx]`, `.[xls]`, or `.[all]`).

### `--output` says path is a directory
Provide an explicit file path (for example `-o result.md`), not a directory path.

### Outlook MSG attachments skipped
This is expected for unsupported attachment types/forms; main email conversion still succeeds with warnings.

---

## 10) Recommended upgrade workflow

```bash
git pull
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[all]"
python -m pytest -q
```
