"""Auto-fix implementation for TRI005 redundant assignments."""

from __future__ import annotations

import re
from pathlib import Path

from .._base import Violation


def apply_fixes(filepath: Path, violations: list[Violation], source: str) -> bool:
    """Apply auto-fixes for redundant assignment violations.

    This is a conservative implementation that only fixes violations marked
    as fixable by the semantic analysis. It inlines simple, redundant
    assignments by:
    1. Replacing the variable usage with the RHS expression
    2. Removing the assignment line

    Args:
        filepath: Path to file to fix
        violations: List of violations to fix
        source: Original source code

    Returns:
        True if fixes were successfully applied, False otherwise
    """
    # Filter to only fixable violations
    fixable_violations = [v for v in violations if v.fixable]

    if not fixable_violations:
        return False

    source_lines = source.splitlines(keepends=True)

    # Sort violations by line number (descending) to avoid line number shifts
    # when we remove assignment lines
    fixable_violations.sort(key=lambda v: v.line, reverse=True)

    fixed_any = False

    for violation in fixable_violations:
        # Extract lifecycle data
        fix_data = violation.fix_data
        if not fix_data or "lifecycle" not in fix_data:
            continue

        lifecycle = fix_data["lifecycle"]
        assignment = lifecycle.assignment
        uses = lifecycle.uses

        # Safety check: should have exactly one use
        if len(uses) != 1:
            continue

        use = uses[0]

        # Get assignment and use lines (convert to 0-indexed)
        assign_line_idx = assignment.line - 1
        use_line_idx = use.line - 1

        if assign_line_idx < 0 or assign_line_idx >= len(source_lines):
            continue
        if use_line_idx < 0 or use_line_idx >= len(source_lines):
            continue

        # Get the RHS expression
        rhs_source = assignment.rhs_source.strip()
        var_name = assignment.var_name

        # Check if inlining is safe
        if not _can_safely_inline(var_name, rhs_source, use_line_idx, source_lines):
            continue

        # Perform the inline replacement
        use_line = source_lines[use_line_idx]

        # Replace the variable at the specific column offset
        # This ensures we replace the right occurrence (e.g., in `func(x=x)`,
        # we replace the value `x`, not the keyword argument name `x`)
        col_offset = use.col

        # Build the replacement: before + rhs + after
        before = use_line[:col_offset]
        after = use_line[col_offset + len(var_name) :]
        new_use_line = before + rhs_source + after

        source_lines[use_line_idx] = new_use_line

        # Remove the assignment line
        source_lines[assign_line_idx] = ""

        fixed_any = True

    if fixed_any:
        # Write the fixed source back to file
        new_source = "".join(source_lines)

        # Remove consecutive blank lines created by removing assignments
        new_source = re.sub(r"\n\n\n+", "\n\n", new_source)

        filepath.write_text(new_source)
        return True

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
