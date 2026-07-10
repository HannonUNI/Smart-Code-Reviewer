# Smart Code Reviewer

A lightweight AI‑assistant that reviews Python code for **readability**, **structure**, and **maintainability** *before* a human review.It runs locally, combines battle‑tested linters (flake8, radon) with custom AST checks, and produces a colourised report.

> **Note:** This tool is designed for **local development** – not for deployment. It’s meant to be run on your machine as a quick pre‑review step.

---

## Features

- **Style** – PEP8 violations (flake8)
- **Complexity** – Cyclomatic complexity per function (radon cc)
- **Maintainability** – Maintainability Index per file (radon mi)
- **Readability** – Overly long functions (>30 lines), too many arguments (>5), missing docstrings (AST)
- **Duplicates** – Identical function bodies across the codebase (AST + hashing)
- **Metrics** – Raw LOC, comments, blank lines per file (radon raw)
- **Coloured Output** – Easy‑to‑scan terminal report with categories (ERROR, WARNING, INFO)

---

## Requirements

- Python 3.6+
- [flake8](https://flake8.pycqa.org/)
- [radon](https://radon.readthedocs.io/)

---

## Installation

1. Clone or download this script (`reviewer.py`).
2. Install the required packages:

```bash
pip install flake8 radon
```


## Usage

Run the reviewer on a single Python file or an entire directory:

**bash**

```
python reviewer.py path/to/your/file.py
# or
python reviewer.py path/to/your/project/
```


## Example Output

**text**

```
🔍 Starting Smart Code Review...
   Running flake8...
   Running radon cc...
   Running radon mi...
   Running custom readability checks...
   Running duplicate function detection...
   Gathering raw metrics (radon raw)...
   Review complete.

📋 Smart Code Reviewer Report
============================================================

⚠️  WARNING (3 issues)
   • utils.py:42 – function 'process_data' has high complexity (14)
   • core.py:15:8 – E501 line too long (85 > 79 characters)
   • core.py:120 – function 'run_all' is 45 lines long (max 30)

ℹ️  INFO (2 issues)
   • models.py:8 – class 'User' is missing a docstring
   • helpers.py:33 – function 'helper' is missing a docstring

📊 Raw Metrics (radon raw):
   core.py: LOC=120, comments=18, blanks=22
   utils.py: LOC=85, comments=10, blanks=15

💡 Suggestions:
   - Fix all ERROR and WARNING items before human review.
   - Prioritise complexity, maintainability, and duplicate warnings.
   - Consider adding docstrings and refactoring long functions.
   - Run the tool again after fixing to verify improvements.
```


## How It Works

The tool runs a series of checks in sequence:

1. **flake8** – catches style issues (line length, indentation, unused imports, etc.).
2. **radon cc** – flags functions with cyclomatic complexity > 10.
3. **radon mi** – warns about files with a Maintainability Index below 40 (and very low below 20).
4. **Custom AST traversal** – checks for:
   * Functions longer than 30 lines
   * Functions with more than 5 arguments
   * Missing docstrings for functions and classes
5. **Duplicate detection** – extracts and normalises function bodies, hashes them, and reports any exact duplicates (ignoring comments and whitespace).
6. **radon raw** – displays lines of code, comments, and blank lines per file (informational only).

All results are aggregated and printed with colour‑coded severity.

---

## Configuration

You can adjust thresholds directly in the script:

| Check                   | Variable / Threshold                | Location                |
| ----------------------- | ----------------------------------- | ----------------------- |
| Flake8 line length      | `--max-line-length=120`           | `run_flake8()`        |
| Max function lines      | `30`                              | `visit_FunctionDef()` |
| Max arguments           | `5`                               | `visit_FunctionDef()` |
| Complexity warning      | `> 10`                            | `run_radon_cc()`      |
| Maintainability warning | `< 40` (low), `< 20` (very low) | `run_radon_mi()`      |

Feel free to tweak these values to match your team's standards.

---

## Limitations

* No web UI – purely command‑line.
* Duplicate detection is **exact‑match only** (not semantic).
* Does not automatically fix issues – it only reports them.
* Requires external tools (`flake8`, `radon`) to be installed.

---

## Contributing

This is a small, educational tool. If you want to extend it, consider:

* Adding a `--json` flag for machine‑readable output.
* Integrating `pylint` or `bandit` for security checks.
* Adding a configuration file (`.reviewerrc`) to customise thresholds.

Pull requests and ideas are welcome!

---

## License

MIT – feel free to use and modify.
