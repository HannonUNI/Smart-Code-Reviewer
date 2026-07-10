# Smart Code Reviewer

A lightweight local review helper for Python code that checks **readability**, **structure**, and **maintainability** before a human review. It runs locally, combines flake8 and radon with custom AST checks, and produces a coloured terminal report.

> **Note:** This tool is designed for **local development** – not for deployment. It’s meant to be run on your machine as a quick pre‑review step.

## Project Structure

The reviewer is split into three modules:

- **`reviewer.py`** – main CLI script that runs the static checks, aggregates findings, and prints the report.
- **`external_tools.py`** – thin wrappers around flake8 and radon so the main script can collect issues in a consistent format.
- **`ai_reviewer.py`** – optional module that handles AI‑powered review using the OpenAI API. It is only used when the `--ai` flag is supplied.

This separation keeps the core logic clean and makes it easier to swap out or extend each part later.

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


## AI‑Powered Review (Optional)

To enable the AI review:

1. Install the optional OpenAI library: `pip install openai`
2. Set your `OPENAI_API_KEY` environment variable.
3. Create a prompt file (default: `ai_prompt.txt`) with your instructions.
4. Run the reviewer with the `--ai` flag (and optionally `--prompt` to choose a different prompt file):
   ```bash
   python reviewer.py my_project/ --ai --prompt ai_prompt.txt
   ```

---



## Requirements

- Python 3.6+
- [flake8](https://flake8.pycqa.org/)
- [radon](https://radon.readthedocs.io/)
- [openai](https://pypi.org/project/openai/) (optional, only for AI review)

---

## Installation

1. Clone or download this script (`reviewer.py`).
2. Install the required packages:

```bash
pip install flake8 radon
```

For AI review, install the optional dependency as well:

```bash
pip install openai
```

## Usage

Run the reviewer on a single Python file or an entire directory:

```bash
python reviewer.py path/to/your/file.py
# or
python reviewer.py path/to/your/project/
```

To add AI feedback:

```bash
python reviewer.py path/to/your/project/ --ai
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

---

🤖 AI Review Feedback:
======================================================================

**Strengths:**
- The code is straightforward and easy to follow for basic arithmetic operations.
- Function names are clear and self‑documenting (`add`, `subtract`, etc.).

**Areas for improvement:**

1. **Error Handling**  
   - The `divide` function prints a message and returns `None` when dividing by zero. This is fragile – the caller might not expect `None` and could cause a `TypeError` later.  
   - **Recommendation:** Raise a custom exception (e.g., `ZeroDivisionError`) to make the failure explicit and let the caller decide how to handle it.

2. **Code Duplication / Extensibility**  
   - The `calculate` function uses a chain of `if/elif` statements. Adding a new operation would require modifying this function, which violates the Open/Closed principle.  
   - **Recommendation:** Use a dictionary mapping operation names to functions, or implement a simple strategy pattern. This would make the code more maintainable.

3. **Global Execution**  
   - The example usage at the bottom runs immediately when the module is imported. This is not good practice for a reusable module.  
   - **Recommendation:** Wrap the demo code inside a `if __name__ == "__main__":` guard.

4. **Type Hints**  
   - The code lacks type annotations, which would improve readability and enable static type checking.  
   - **Recommendation:** Add type hints for all function arguments and return values (e.g., `def add(a: int, b: int) -> int:`).

5. **Logging vs. Printing**  
   - Using `print` for error messages is fine for a toy script, but in a larger application, consider using Python’s `logging` module for better control over output.

**Overall:**  
The code is functional and clear, but it would benefit from better error handling, a more extensible architecture, and protective execution guards. With these tweaks, it would be production‑ready.
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
