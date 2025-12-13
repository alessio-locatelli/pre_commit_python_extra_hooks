"""Safe autofix implementation for function renames."""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

from .analysis import Suggestion, read_source

logger = logging.getLogger("validate-function-name")


def _count_nesting_depth(func_node: ast.FunctionDef) -> int:
    """Calculate maximum nesting depth of control flow in function.

    Args:
        func_node: Function AST node

    Returns:
        Maximum nesting depth (0 = no nesting, 1 = single level, etc.)
    """
    max_depth = 0

    def _walk_depth(node: ast.AST, current_depth: int) -> None:
        nonlocal max_depth
        max_depth = max(max_depth, current_depth)

        # Increase depth for control flow structures
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            for child in ast.iter_child_nodes(node):
                _walk_depth(child, current_depth + 1)
        else:
            for child in ast.iter_child_nodes(node):
                _walk_depth(child, current_depth)

    # Start from function body
    for stmt in func_node.body:
        _walk_depth(stmt, 0)

    return max_depth


def _count_returns(func_node: ast.FunctionDef) -> int:
    """Count number of return statements in function.

    Args:
        func_node: Function AST node

    Returns:
        Number of return statements
    """
    return sum(1 for node in ast.walk(func_node) if isinstance(node, ast.Return))


def _count_function_lines(func_node: ast.FunctionDef) -> int:
    """Count lines of code in function, excluding docstring.

    Args:
        func_node: Function AST node

    Returns:
        Number of lines (excluding docstring)
    """
    # Check if first statement is a docstring
    docstring_lines = 0
    if (
        func_node.body
        and isinstance(func_node.body[0], ast.Expr)
        and isinstance(func_node.body[0].value, ast.Constant)
        and isinstance(func_node.body[0].value.value, str)
    ):
        # Count docstring lines
        docstring_node = func_node.body[0]
        docstring_lines = docstring_node.end_lineno - docstring_node.lineno + 1  # type: ignore[operator]

    # Total function lines
    total_lines = func_node.end_lineno - func_node.lineno + 1  # type: ignore[operator]

    # Subtract docstring lines
    return total_lines - docstring_lines


def should_autofix(filepath: Path, suggestion: Suggestion) -> bool:
    """Determine if a suggestion is safe to auto-fix.

    Safe autofix criteria (ALL must be met):
    1. High confidence (not "no confident suggestion")
    2. Function is small (< 20 lines of code, excluding docstring)
    3. Simple control flow (max nesting depth ≤ 1)
    4. Single return point (at most one return statement)

    Args:
        filepath: Path to the file containing the function
        suggestion: Naming suggestion to evaluate

    Returns:
        True if safe to auto-fix, False otherwise
    """
    # Check 1: Confidence
    if suggestion.reason == "no confident suggestion":
        return False

    # Parse file and find the function
    try:
        source = read_source(filepath)
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeDecodeError) as error:
        logger.warning("Filepath: %s. Error: %s", filepath, repr(error))
        return False

    # Find the specific function
    func_node: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == suggestion.func_name
            and node.lineno == suggestion.lineno
        ):
            func_node = node
            break

    if func_node is None:
        return False

    # Check 2: Size (< 20 lines excluding docstring)
    line_count = _count_function_lines(func_node)
    if line_count >= 20:
        return False

    # Check 3: Complexity (nesting depth ≤ 1)
    nesting = _count_nesting_depth(func_node)
    if nesting > 1:
        return False

    # Check 4: Single return (≤ 1 return statement)
    returns = _count_returns(func_node)
    return returns <= 1


def apply_fix(filepath: Path, suggestion: Suggestion) -> bool:
    """Apply a rename fix to a file.

    Strategy: Word-boundary replacement of function name using regex.

    Args:
        filepath: Path to the file to fix
        suggestion: Naming suggestion to apply

    Returns:
        True if fix was applied successfully, False otherwise
    """
    try:
        source = read_source(filepath)
    except (OSError, UnicodeDecodeError) as error:
        logger.warning("Filepath: %s. Error: %s", filepath, repr(error))
        return False

    # Word-boundary regex to avoid renaming parts of other identifiers
    # E.g., "get_user" should not rename "get_username"
    pattern = re.compile(rf"\b{re.escape(suggestion.func_name)}\b")

    # Apply replacement
    new_source = pattern.sub(suggestion.suggested_name, source)

    # Check if anything was changed
    if new_source == source:
        return False

    # Write back
    try:
        filepath.write_text(new_source, encoding="utf8")
        return True
    except OSError as os_error:
        logger.warning("Filepath: %s. Error: %s", filepath, repr(os_error))
        return False
