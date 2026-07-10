import subprocess
from pathlib import Path
from fnmatch import fnmatchcase
from dataclasses import dataclass


@dataclass
class ReviewConfig:
    max_function_lines: int = 30
    max_function_args: int = 5
    complexity_threshold: int = 10
    maintainability_low_threshold: float = 40.0
    maintainability_very_low_threshold: float = 20.0
    flake8_max_line_length: int = 120


def _load_ignored_patterns(target_path):
    """Load ignore patterns from .gitignore files above the target path."""
    target = Path(target_path)
    if target.is_file():
        base = target.parent
    elif target.is_dir():
        base = target
    else:
        base = Path(target_path).parent if hasattr(target_path, 'parent') else Path('.')

    root = base.resolve()
    patterns = {'.venv', 'venv'}
    current = root
    while True:
        gitignore = current / '.gitignore'
        if gitignore.exists():
            with open(gitignore, 'r', encoding='utf-8') as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith('#') or line.startswith('!'):
                        continue
                    patterns.add(line.rstrip('/'))
        if current == current.parent:
            break
        current = current.parent
    return patterns, root


def _is_ignored(path, root, patterns):
    """Return True when a path matches any ignore pattern or common virtualenv folder."""
    rel_path = path.resolve().relative_to(root).as_posix()
    parts = Path(rel_path).parts
    for pattern in patterns:
        normalized = pattern.lstrip('/')
        if not normalized:
            continue
        if '/' in normalized:
            if fnmatchcase(rel_path, normalized) or fnmatchcase(rel_path, f'**/{normalized}'):
                return True
        else:
            if any(fnmatchcase(part, normalized) for part in parts):
                return True
            if normalized in parts:
                return True
    return False


def collect_python_files(target_path):
    """Return Python files under the target, skipping ignored paths and virtualenv folders."""
    target = Path(target_path)
    patterns, root = _load_ignored_patterns(target)
    if target.is_file() and target.suffix == '.py':
        return [target] if not _is_ignored(target, root, patterns) else []
    if target.is_dir():
        return [
            path for path in target.rglob('*.py')
            if not _is_ignored(path, root, patterns)
        ]
    return []


def run_flake8(target, config=None):
    """Run flake8 and return list of issues."""
    files = collect_python_files(target)
    if not files:
        return []

    config = config or ReviewConfig()
    try:
        result = subprocess.run(
            ['flake8', *[str(path) for path in files], f'--max-line-length={config.flake8_max_line_length}', '--extend-ignore=E203,W503'],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        return [("flake8 not installed. Run: pip install flake8", None, None, 'ERROR')]

    issues = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        parts = line.split(':', 3)  # file:line:col: message
        if len(parts) >= 4:
            file_path = parts[0]
            line_no = parts[1]
            col_no = parts[2]
            msg = parts[3].strip()
            issues.append((f"{file_path}:{line_no}:{col_no} {msg}", line_no, col_no, 'STYLE'))
        else:
            issues.append((line, None, None, 'STYLE'))
    return issues

def run_radon_cc(target, config=None):
    """Run radon cc (cyclomatic complexity) and return issues."""
    files = collect_python_files(target)
    if not files:
        return []

    config = config or ReviewConfig()
    try:
        result = subprocess.run(
            ['radon', 'cc', *[str(path) for path in files], '-a', '-s'],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        return [("radon not installed. Run: pip install radon", None, None, 'ERROR')]

    issues = []
    for line in result.stdout.splitlines():
        if ' - ' in line and '(' in line:
            parts = line.split(' - ')
            if len(parts) == 2:
                location = parts[0].strip()
                rest = parts[1].strip()
                if ' (' in rest:
                    func_name = rest.split(' (')[0]
                    complex_str = rest.split('(')[-1].rstrip(')')
                    if complex_str.isdigit():
                        comp = int(complex_str)
                        if comp > config.complexity_threshold:
                            issues.append(
                                (f"{location} - function '{func_name}' has high complexity ({comp})",
                                 None, None, 'COMPLEXITY')
                            )
    return issues

def run_radon_mi(target, config=None):
    """Run radon mi (maintainability index) and return issues."""
    files = collect_python_files(target)
    if not files:
        return []

    config = config or ReviewConfig()
    try:
        result = subprocess.run(
            ['radon', 'mi', *[str(path) for path in files], '-s'],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        return []

    issues = []
    for line in result.stdout.splitlines():
        if ' - ' in line and '(' in line:
            parts = line.split(' - ')
            if len(parts) == 2:
                file_name = parts[0].strip()
                rest = parts[1].strip()
                if ' (' in rest:
                    grade = rest.split(' (')[0]
                    score_str = rest.split('(')[-1].rstrip(')')
                    try:
                        score = float(score_str)
                        if score < config.maintainability_very_low_threshold:
                            issues.append(
                                (f"{file_name} - maintainability index {score:.1f} (grade {grade}) - very low",
                                 None, None, 'MAINTAINABILITY')
                            )
                        elif score < config.maintainability_low_threshold:
                            issues.append(
                                (f"{file_name} - maintainability index {score:.1f} (grade {grade}) - low",
                                 None, None, 'MAINTAINABILITY')
                            )
                    except ValueError:
                        pass
    return issues

def run_radon_raw(target):
    """Run radon raw and return a dictionary of metrics per file."""
    files = collect_python_files(target)
    if not files:
        return {}

    try:
        result = subprocess.run(
            ['radon', 'raw', *[str(path) for path in files], '-s'],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        return {"error": "radon not installed. Run: pip install radon"}

    metrics = {}
    current_file = None
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        if not line.startswith(' ') and ':' not in line and not line.startswith('    '):
            current_file = line.strip()
            metrics[current_file] = {}
        elif current_file and ':' in line:
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                try:
                    metrics[current_file][key] = int(value)
                except ValueError:
                    metrics[current_file][key] = value
    return metrics