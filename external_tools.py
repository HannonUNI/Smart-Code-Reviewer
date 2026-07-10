import subprocess

def run_flake8(target):
    """Run flake8 and return list of issues."""
    try:
        result = subprocess.run(
            ['flake8', target, '--max-line-length=120', '--extend-ignore=E203,W503'],
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

def run_radon_cc(target):
    """Run radon cc (cyclomatic complexity) and return issues."""
    try:
        result = subprocess.run(
            ['radon', 'cc', target, '-a', '-s'],
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
                        if comp > 10:
                            issues.append(
                                (f"{location} - function '{func_name}' has high complexity ({comp})",
                                 None, None, 'COMPLEXITY')
                            )
    return issues

def run_radon_mi(target):
    """Run radon mi (maintainability index) and return issues."""
    try:
        result = subprocess.run(
            ['radon', 'mi', target, '-s'],
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
                        if score < 20:
                            issues.append(
                                (f"{file_name} - maintainability index {score:.1f} (grade {grade}) - very low",
                                 None, None, 'MAINTAINABILITY')
                            )
                        elif score < 40:
                            issues.append(
                                (f"{file_name} - maintainability index {score:.1f} (grade {grade}) - low",
                                 None, None, 'MAINTAINABILITY')
                            )
                    except ValueError:
                        pass
    return issues

def run_radon_raw(target):
    """Run radon raw and return a dictionary of metrics per file."""
    try:
        result = subprocess.run(
            ['radon', 'raw', target, '-s'],
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