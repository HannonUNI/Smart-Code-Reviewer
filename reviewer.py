#!/usr/bin/env python3
"""
Smart Code Reviewer, a review assistant for Python code.
Checks style, complexity, maintainability, readability, duplicates, and raw metrics.
"""

import ast
import sys
import os
from pathlib import Path
from collections import defaultdict
import hashlib
import re
from external_tools import collect_python_files, run_flake8, run_radon_cc, run_radon_mi, run_radon_raw
import argparse

try:
    from ai_reviewer import run_ai_review
except ImportError:
    # Fallback if ai_reviewer.py is missing
    def run_ai_review(target_path, prompt_file="ai_prompt.txt"):
        return "ai_reviewer.py not found. AI review disabled."

# ---------- Duplicate detection ----------
def get_function_body(filename, node):
    """Extract the source lines of a function body (excluding decorators and signature)."""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    start_line = node.body[0].lineno - 1
    end_line = node.end_lineno
    body_lines = lines[start_line:end_line]
    if body_lines:
        stripped = [l.rstrip() for l in body_lines if l.strip()]
        if stripped:
            indent = len(stripped[0]) - len(stripped[0].lstrip())
            dedented = [l[indent:] if l.startswith(' ' * indent) else l for l in body_lines]
            body_text = ''.join(dedented)
        else:
            body_text = ''.join(body_lines)
    else:
        body_text = ''
    body_text = re.sub(r'#.*$', '', body_text, flags=re.MULTILINE)
    body_text = re.sub(r'\n\s*\n', '\n', body_text).strip()
    return body_text

def find_duplicate_functions(target_path):
    """Find functions with identical bodies across all Python files."""
    target = Path(target_path)
    files = collect_python_files(target)
    if not files and target.exists():
        return []

    all_funcs = {}
    issues = []

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                body_text = get_function_body(file_path, node)
                if not body_text:
                    continue
                body_hash = hashlib.md5(body_text.encode('utf-8')).hexdigest()
                key = (body_hash, node.name)
                all_funcs.setdefault(key, []).append((str(file_path), node.lineno, node.name))

    for (hash_val, func_name), occurrences in all_funcs.items():
        if len(occurrences) > 1:
            locations = ', '.join([f"{f}:{l}" for f, l, n in occurrences])
            issues.append(
                (f"Duplicate function '{func_name}' found at: {locations}",
                 None, None, 'DUPLICATE')
            )

    return issues

# ---------- Custom AST checks ----------
class ReadabilityVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.issues = []

    def visit_FunctionDef(self, node):
        line_count = node.end_lineno - node.lineno + 1
        if line_count > 30:
            self.issues.append(
                (f"{self.filename}:{node.lineno} - function '{node.name}' is {line_count} lines long (max 30)",
                 node.lineno, None, 'READABILITY')
            )
        num_args = len(node.args.args)
        if num_args > 5:
            self.issues.append(
                (f"{self.filename}:{node.lineno} - function '{node.name}' has {num_args} arguments (max 5)",
                 node.lineno, None, 'READABILITY')
            )
        if not ast.get_docstring(node):
            self.issues.append(
                (f"{self.filename}:{node.lineno} - function '{node.name}' is missing a docstring",
                 node.lineno, None, 'DOCUMENTATION')
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if not ast.get_docstring(node):
            self.issues.append(
                (f"{self.filename}:{node.lineno} - class '{node.name}' is missing a docstring",
                 node.lineno, None, 'DOCUMENTATION')
            )
        self.generic_visit(node)

def custom_checks(target_path):
    all_issues = []
    target = Path(target_path)
    files = collect_python_files(target)
    if not files:
        print(f"Error: {target_path} is not a Python file or directory.")
        return []

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            visitor = ReadabilityVisitor(str(file_path))
            visitor.visit(tree)
            all_issues.extend(visitor.issues)
        except SyntaxError as e:
            all_issues.append((f"{file_path}:{e.lineno} - Syntax error: {e.msg}", e.lineno, None, 'ERROR'))
        except Exception as e:
            all_issues.append((f"{file_path} - Could not parse: {e}", None, None, 'ERROR'))
    return all_issues

# ---------- Report generation ----------
def print_report(all_issues, raw_metrics=None, ai_response=None):
    """Print a coloured, grouped report with optional raw metrics and AI feedback."""
    if not all_issues and not raw_metrics and not ai_response:
        print("✅ No issues found! Code looks clean.")
        return

    # Group issues by severity
    groups = defaultdict(list)
    for issue in all_issues:
        msg, line, col, category = issue
        if category == 'ERROR':
            severity = '❌ ERROR'
        elif category in ('STYLE', 'COMPLEXITY', 'MAINTAINABILITY', 'DUPLICATE'):
            severity = '⚠️  WARNING'
        else:
            severity = 'ℹ️  INFO'
        groups[severity].append((msg, line, col))

    print("\n📋 Smart Code Reviewer Report")
    print("=" * 60)

    for severity, items in groups.items():
        print(f"\n{severity} ({len(items)} issues)")
        for msg, line, col in items:
            loc = ""
            if line:
                loc = f" line {line}"
                if col:
                    loc += f", col {col}"
            print(f"   • {msg}{loc}")

    # Print raw metrics if available and not an error
    if raw_metrics and 'error' not in raw_metrics:
        print("\n📊 Raw Metrics (radon raw):")
        for file, metrics in raw_metrics.items():
            loc = metrics.get('LOC', 0)
            comments = metrics.get('comments', 0)
            blanks = metrics.get('blank', 0)
            print(f"   {file}: LOC={loc}, comments={comments}, blanks={blanks}")

    print("\n" + "💡 Suggestions:")
    print("   - Fix all ERROR and WARNING items before human review.")
    print("   - Prioritise complexity, maintainability, and duplicate warnings.")
    print("   - Consider adding docstrings and refactoring long functions.")
    print("   - Run the tool again after fixing to verify improvements.")

    if ai_response:
        print("\n🤖 AI Review Feedback:")
        print("=" * 70)
        print(ai_response)

# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(description="Smart Code Reviewer")
    parser.add_argument("target", help="Path to a Python file or directory")
    parser.add_argument("--ai", action="store_true", help="Enable AI-powered review (requires OpenAI API key and prompt file)")
    parser.add_argument("--prompt", default="ai_prompt.txt", help="Prompt file for AI review (default: ai_prompt.txt)")
    args = parser.parse_args()

    target = args.target
    if not os.path.exists(target):
        print(f"Error: '{target}' does not exist.")
        sys.exit(1)

    print("🔍 Starting Smart Code Review...")
    all_issues = []

    print("   Running flake8...")
    flake_issues = run_flake8(target)
    all_issues.extend(flake_issues)

    print("   Running radon cc...")
    cc_issues = run_radon_cc(target)
    all_issues.extend(cc_issues)

    print("   Running radon mi...")
    mi_issues = run_radon_mi(target)
    all_issues.extend(mi_issues)

    print("   Running custom readability checks...")
    custom_issues = custom_checks(target)
    all_issues.extend(custom_issues)

    print("   Running duplicate function detection...")
    dup_issues = find_duplicate_functions(target)
    all_issues.extend(dup_issues)

    print("   Gathering raw metrics (radon raw)...")
    raw_metrics = run_radon_raw(target)

    ai_response = None
    if args.ai:
        print("   Running AI review (this may take a moment)...")
        ai_response = run_ai_review(target, args.prompt)

    print("   Review complete.")
    print_report(all_issues, raw_metrics, ai_response)

if __name__ == "__main__":
    main()