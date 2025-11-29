"""Pre-commit hook to forbid meaningless variable names like 'data' and 'result'."""

import argparse
import ast
import io
import re
import sys
import tokenize
from typing import Sequence

# Regex pattern for inline ignore comments (case-insensitive)
IGNORE_PATTERN = re.compile(
    r"#\s*maintainability:\s*ignore\[meaningless-variable-name\]", re.IGNORECASE
)

# Default forbidden variable names
DEFAULT_FORBIDDEN_NAMES = {"data", "result"}


class ForbiddenNameVisitor(ast.NodeVisitor):
    """
    AST visitor that detects forbidden variable names in Python code.

    This visitor checks all contexts where variables are defined:
    - Regular assignments (data = 1)
    - Annotated assignments (data: int = 1)
    - Function parameters (def foo(data):)
    - Async function parameters (async def foo(data):)
    """

    def __init__(self, forbidden_names: set[str]) -> None:
        """
        Initialize the visitor with a set of forbidden names.

        Args:
            forbidden_names: Set of variable names that are not allowed
        """
        self.forbidden_names = forbidden_names
        self.violations: list[dict[str, str | int]] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        """
        Visit regular assignment nodes: data = 1, x, data = (1, 2).

        Args:
            node: The Assign AST node
        """
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._check_name(target.id, node.lineno)
            elif isinstance(target, (ast.Tuple, ast.List)):
                # Handle multiple assignment: data, result = get_values()
                for element in target.elts:
                    if isinstance(element, ast.Name):
                        self._check_name(element.id, element.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """
        Visit annotated assignment nodes: data: int = 1.

        Args:
            node: The AnnAssign AST node
        """
        if isinstance(node.target, ast.Name):
            self._check_name(node.target.id, node.lineno)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Visit function definition nodes: def foo(data):.

        Args:
            node: The FunctionDef AST node
        """
        self._check_function_args(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """
        Visit async function definition nodes: async def foo(data):.

        Args:
            node: The AsyncFunctionDef AST node
        """
        self._check_function_args(node)
        self.generic_visit(node)

    def _check_function_args(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """
        Check all function arguments for forbidden names.

        Handles all argument types:
        - Positional: def foo(data)
        - Positional-only: def foo(data, /)
        - Keyword-only: def foo(*, data)
        - Variable positional: def foo(*data)
        - Variable keyword: def foo(**data)

        Args:
            node: The FunctionDef or AsyncFunctionDef AST node
        """
        # Regular positional arguments
        for arg in node.args.args:
            self._check_name(arg.arg, node.lineno)

        # Positional-only arguments (Python 3.8+)
        for arg in node.args.posonlyargs:
            self._check_name(arg.arg, node.lineno)

        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            self._check_name(arg.arg, node.lineno)

        # *args parameter
        if node.args.vararg:
            self._check_name(node.args.vararg.arg, node.lineno)

        # **kwargs parameter
        if node.args.kwarg:
            self._check_name(node.args.kwarg.arg, node.lineno)

    def _check_name(self, name: str, lineno: int) -> None:
        """
        Check if a variable name is forbidden and record violation.

        Args:
            name: The variable name to check
            lineno: The line number where the name appears
        """
        if name in self.forbidden_names:
            self.violations.append({"name": name, "line": lineno})


def get_ignored_lines(source: str) -> set[int]:
    """
    Extract line numbers that have inline ignore comments.

    Uses the tokenize module to accurately detect comments (not strings).

    Args:
        source: Python source code as string

    Returns:
        Set of line numbers with ignore comments
    """
    ignored = set()

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)

        for tok_type, tok_string, (line, _), _, _ in tokens:
            if tok_type != tokenize.COMMENT:
                continue

            if IGNORE_PATTERN.search(tok_string):
                ignored.add(line)
    except tokenize.TokenError:
        # If tokenization fails, return empty set (no lines ignored)
        pass

    return ignored


def check_file(filepath: str, forbidden_names: set[str]) -> list[dict[str, str | int]]:
    """
    Check a Python file for forbidden variable names.

    Args:
        filepath: Path to the Python file to check
        forbidden_names: Set of forbidden variable names

    Returns:
        List of violations (each with 'name' and 'line' keys)
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except (OSError, UnicodeDecodeError):
        # If we can't read the file, skip it
        return []

    # Parse file to get ignored lines
    ignored_lines = get_ignored_lines(source)

    # Parse AST and find violations
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        # If file has syntax errors, skip it (not our job to validate syntax)
        return []

    visitor = ForbiddenNameVisitor(forbidden_names)
    visitor.visit(tree)

    # Filter out violations on ignored lines
    violations = [v for v in visitor.violations if v["line"] not in ignored_lines]

    return violations


def report_violation(filepath: str, line: int, name: str) -> None:
    """
    Report a single violation with helpful message and link.

    Follows standard linter format: filepath:line: message

    Args:
        filepath: Path to the file containing the violation
        line: Line number where the violation occurs
        name: The forbidden variable name found
    """
    message = (
        f"Forbidden variable name '{name}' found. "
        f"Use a more descriptive name or add "
        f"'# maintainability: ignore[meaningless-variable-name]' to suppress. "
        f"See https://hilton.org.uk/blog/meaningless-variable-names"
    )
    print(f"{filepath}:{line}: {message}")


def main(argv: Sequence[str] | None = None) -> int:
    """
    Main entry point for the forbid-vars hook.

    Args:
        argv: Command-line arguments (defaults to sys.argv if None)

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    parser = argparse.ArgumentParser(
        description="Check for forbidden variable names in Python files"
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check")
    parser.add_argument(
        "--names",
        default="data,result",
        help="Comma-separated list of forbidden names (default: data,result)",
    )

    args = parser.parse_args(argv)

    # Parse forbidden names from argument
    forbidden_names = {n.strip() for n in args.names.split(",") if n.strip()}

    if not forbidden_names:
        # If no forbidden names provided, exit successfully
        return 0

    # Check all files
    failed = False
    for filepath in args.filenames:
        violations = check_file(filepath, forbidden_names)
        if violations:
            failed = True
            for violation in violations:
                report_violation(filepath, violation["line"], violation["name"])

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
