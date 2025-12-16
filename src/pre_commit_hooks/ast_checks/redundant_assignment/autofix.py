"""Auto-fix implementation for TRI005 redundant assignments."""

from __future__ import annotations

from pathlib import Path

from .._base import Violation


def apply_fixes(filepath: Path, violations: list[Violation], source: str) -> bool:
    """Apply auto-fixes for redundant assignment violations.

    This is a conservative implementation that only fixes violations marked
    as fixable by the semantic analysis. It inlines simple, redundant
    assignments by:
    1. Replacing the variable usage with the RHS expression
    2. Removing the assignment line

    IMPORTANT: Due to complexity of control flow and potential for breaking code,
    autofix is currently DISABLED. This function returns False to prevent any
    automatic modifications until the autofix logic is thoroughly tested and
    validated against all edge cases.

    Args:
        filepath: Path to file to fix
        violations: List of violations to fix
        source: Original source code

    Returns:
        True if fixes were successfully applied, False otherwise
    """
    # DISABLED: Autofix has edge cases that can break code
    # - Word boundary issues (replacing 'x' can affect 'max', 'index', etc.)
    # - Multiple occurrences on same line
    # - Indentation and formatting issues
    # - Control flow complications
    #
    # Users should manually review and fix violations, or use inline suppressions
    return False


def _can_safely_inline(
    var_name: str,
    rhs_source: str,
    use_line_idx: int,
    source_lines: list[str],
) -> bool:
    """Check if inlining is safe (no line length violations, comments intact, etc.).

    Args:
        var_name: Variable name being inlined
        rhs_source: RHS source code to inline
        use_line_idx: Line index where variable is used (0-indexed)
        source_lines: List of source code lines

    Returns:
        True if safe to inline
    """
    if use_line_idx < 0 or use_line_idx >= len(source_lines):
        return False

    # Get the line where variable is used
    use_line = source_lines[use_line_idx]

    # Estimate new line length after inlining
    # Change: remove var_name (len(var_name)) and add rhs_source (len(rhs_source))
    len_diff = len(rhs_source) - len(var_name)
    new_line_len = len(use_line.rstrip("\n\r")) + len_diff

    # Check if new line would exceed reasonable length (88 chars, Black's default)
    if new_line_len > 88:
        return False

    # Check if the RHS expression contains newlines (multiline expressions)
    # These are complex and shouldn't be auto-fixed
    return not ("\n" in rhs_source or "\r" in rhs_source)
