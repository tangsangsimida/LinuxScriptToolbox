#!/usr/bin/env python3
"""Static analysis script to enforce UI patterns in tool modules.

Checks that tool modules use unified UI interfaces from utils/ui.py
instead of hardcoded menu logic.

Usage:
    python tests/check_ui_patterns.py
    python tests/check_ui_patterns.py --fix  # Show suggestions for fixes
"""

import ast
import sys
from pathlib import Path

# Patterns that should NOT appear in tool modules
FORBIDDEN_PATTERNS = {
    "clear_screen": "Use prompt_selection() instead — it handles screen clearing",
    'input(': "Use ask() or prompt_selection() instead of raw input()",
    '== "back"': "Use BACK_ACTION constant instead of hardcoded string",
    "== 'back'": "Use BACK_ACTION constant instead of hardcoded string",
}

# Functions that should be imported from utils.ui, not called directly
UI_FUNCTIONS = {
    "prompt_selection",
    "confirm",
    "select_option",
    "ask",
    "print_success",
    "print_error",
    "print_info",
    "print_warning",
    "press_any_key",
}

# Constants that should be imported from utils.ui
UI_CONSTANTS = {"BACK_ACTION", "CANCEL_ACTION"}


class UI_pattern_checker(ast.NodeVisitor):
    """AST visitor to check for forbidden UI patterns."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors: list[tuple[int, str, str]] = []
        self.imports: set[str] = set()

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports from utils.ui."""
        if node.module == "utils.ui":
            for alias in node.names:
                self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Check for forbidden function calls."""
        # Check for input() calls
        if isinstance(node.func, ast.Name) and node.func.id == "input":
            self.errors.append(
                (node.lineno, "input()", FORBIDDEN_PATTERNS["input("])
            )
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        """Check for hardcoded string comparisons."""
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(comparator, ast.Constant) and comparator.value == "back":
                self.errors.append(
                    (node.lineno, '== "back"', FORBIDDEN_PATTERNS['== "back"'])
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Check for direct calls to forbidden functions."""
        if isinstance(node.value, ast.Name):
            if node.attr == "clear_screen" and node.value.id != "ui":
                self.errors.append(
                    (node.lineno, "clear_screen()", FORBIDDEN_PATTERNS["clear_screen"])
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check for _show_menu methods (legacy pattern)."""
        if node.name == "_show_menu":
            self.errors.append(
                (node.lineno, "_show_menu()", "Legacy pattern — use prompt_selection() in run()")
            )
        self.generic_visit(node)


def check_file(filepath: Path) -> list[tuple[int, str, str]]:
    """Check a single Python file for UI pattern violations."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        return [(e.lineno or 0, "SyntaxError", str(e))]

    checker = UI_pattern_checker(str(filepath))
    checker.visit(tree)
    return checker.errors


def check_tools_directory(tools_dir: Path) -> dict[str, list[tuple[int, str, str]]]:
    """Check all tool modules in the tools directory."""
    results = {}
    for py_file in tools_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or py_file.name == "__init__.py":
            continue
        if py_file.name == "base.py":
            continue

        errors = check_file(py_file)
        if errors:
            rel_path = py_file.relative_to(tools_dir.parent)
            results[str(rel_path)] = errors

    return results


def main():
    project_dir = Path(__file__).parent.parent
    tools_dir = project_dir / "tools"

    print("Checking UI patterns in tool modules...")
    print("=" * 60)

    results = check_tools_directory(tools_dir)

    if not results:
        print("✓ All tool modules follow UI patterns correctly!")
        return 0

    total_errors = 0
    for filepath, errors in results.items():
        print(f"\n{filepath}:")
        for lineno, pattern, suggestion in errors:
            print(f"  Line {lineno}: {pattern}")
            print(f"    → {suggestion}")
            total_errors += 1

    print("\n" + "=" * 60)
    print(f"Found {total_errors} violation(s) in {len(results)} file(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
