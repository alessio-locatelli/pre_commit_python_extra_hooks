"""Check and fix excessive blank lines after module headers.

TRI002: Collapse 2+ consecutive blank lines after module headers (copyright,
docstring, or comments) to a single blank line.

Inline ignore: # pytriage: ignore=TRI002 (not currently supported)
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

from . import register_check
from ._base import Violation

logger = logging.getLogger("excessive_blank_lines")


def find_module_header_end(lines: list[str]) -> int:
    """Find the line number where module header ends.

    Module header includes: shebang, encoding, docstring, copyright/comments.

    Args:
        lines: List of file lines

    Returns:
        Index (0-based) where module header ends
    """
    in_docstring = False
    docstring_char = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Empty lines in header are ok
        if not stripped:
            continue

        # Shebang and encoding declarations
        if stripped.startswith("#"):
            continue

        # Docstring detection
        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_char = stripped[:3]
            if stripped.count(docstring_char) >= 2 and len(stripped) > 3:
                # Single-line docstring
                continue
            else:
                # Multi-line docstring start
                in_docstring = True
                continue

        # Check for docstring end
        if in_docstring and docstring_char and docstring_char in stripped:
            in_docstring = False
            continue

        # Skip lines inside docstring
        if in_docstring:
            continue

        # First code line (import, class, def, assignment, etc)
        return i

    return len(lines)


def check_file_violations(source: str) -> list[tuple[int, str]]:
    """Check file for excessive blank lines.

    Args:
        source: File source code

    Returns:
        List of (line_number, message) tuples
    """
    lines = source.splitlines(keepends=True)

    if not lines:
        return []

    violations = []
    header_end = find_module_header_end(lines)

    # Find the last non-blank line in the header region
    last_header_line = 0
    for i in range(header_end - 1, -1, -1):
        if lines[i].strip():
            last_header_line = i + 1
            break

    blank_count = 0
    start_blank = None
    found_first_code_line = False

    for i in range(last_header_line, len(lines)):
        line = lines[i]
        if line.strip() == "":
            if blank_count == 0:
                start_blank = i
            blank_count += 1
        else:
            # Non-blank line found
            # Only report violations before the first code line
            if (
                not found_first_code_line
                and blank_count >= 2
                and start_blank is not None
            ):
                # Check if this line is a class or function definition
                # PEP 8 allows 2 blank lines before top-level class/function definitions
                if _is_class_or_function_def(line):
                    # Only report if more than 2 blank lines
                    if blank_count > 2:
                        violations.append(
                            (
                                start_blank + 1,
                                f"Excessive blank lines ({blank_count}) "
                                + "should be collapsed to 2",
                            )
                        )
                else:
                    # For non-class/function definitions, report if >= 2 blank lines
                    violations.append(
                        (
                            start_blank + 1,
                            f"Excessive blank lines ({blank_count}) "
                            + "should be collapsed to 1",
                        )
                    )
            blank_count = 0
            start_blank = None
            found_first_code_line = True

    return violations


def _is_class_or_function_def(line: str) -> bool:
    """Check if a line starts a class or function definition.

    Args:
        line: Source code line

    Returns:
        True if line starts a class or function definition
    """
    stripped = line.lstrip()
    return stripped.startswith(("class ", "def ", "async def "))


def fix_file_content(source: str) -> str:
    """Fix excessive blank lines in source code.

    Args:
        source: Original source code

    Returns:
        Fixed source code
    """
    lines = source.splitlines(keepends=True)

    if not lines:
        return source

    header_end = find_module_header_end(lines)

    # Find the last non-blank line in the header region
    last_header_line = 0
    for i in range(header_end - 1, -1, -1):
        if lines[i].strip():
            last_header_line = i + 1
            break

    # Copy header lines (excluding trailing blank lines)
    new_lines = lines[:last_header_line]

    # Only collapse blank lines between header and first code line
    # After first code line, preserve all blank lines
    blank_count = 0
    found_first_code_line = False
    blank_line_start_idx = last_header_line

    for i in range(last_header_line, len(lines)):
        line = lines[i]
        is_blank = line.strip() == ""

        if is_blank:
            if blank_count == 0:
                blank_line_start_idx = i
            blank_count += 1
            if not found_first_code_line:
                # Before first code line: will handle after we see what comes next
                pass
            else:
                # After first code line: preserve all blank lines
                new_lines.append(line)
        else:
            # Non-blank line found
            if not found_first_code_line and blank_count > 0:
                # Check if this line is a class or function definition
                # PEP 8 requires 2 blank lines before top-level class/function
                # definitions
                if _is_class_or_function_def(line):
                    # Preserve 2 blank lines (or use existing if less than 2)
                    target_blank_count = min(2, blank_count)
                else:
                    # Collapse to 1 blank line
                    target_blank_count = 1

                # Append the appropriate number of blank lines
                for j in range(target_blank_count):
                    if blank_line_start_idx + j < i:
                        new_lines.append(lines[blank_line_start_idx + j])

            blank_count = 0
            found_first_code_line = True
            new_lines.append(line)

    return "".join(new_lines)


@register_check
class ExcessiveBlankLinesCheck:
    """Check for excessive blank lines after module headers."""

    @property
    def check_id(self) -> str:
        """Return check identifier."""
        return "excessive-blank-lines"

    @property
    def error_code(self) -> str:
        """Return error code."""
        return "TRI002"

    def get_prefilter_pattern(self) -> str | None:
        """Return pre-filter pattern.

        Returns None because all files should be checked.
        """
        return None

    def check(self, filepath: Path, tree: ast.Module, source: str) -> list[Violation]:
        """Run check and return violations.

        Args:
            filepath: Path to file
            tree: Parsed AST tree (not used for this check)
            source: Source code

        Returns:
            List of violations
        """
        file_violations = check_file_violations(source)

        violations = []
        for line_num, message in file_violations:
            violations.append(
                Violation(
                    check_id=self.check_id,
                    error_code=self.error_code,
                    line=line_num,
                    col=0,
                    message=message,
                    fixable=True,
                )
            )

        return violations

    def fix(
        self,
        filepath: Path,
        violations: list[Violation],
        source: str,
        tree: ast.Module,
    ) -> bool:
        """Apply fixes for excessive blank lines.

        Args:
            filepath: Path to file
            violations: Violations to fix
            source: Source code
            tree: Parsed AST tree (not used)

        Returns:
            True if fixes were applied successfully
        """
        if not violations:
            return False

        try:
            fixed_content = fix_file_content(source)

            # Write back to file
            filepath.write_text(fixed_content, encoding="utf-8")
            return True
        except OSError as os_error:
            logger.error("Failed to write %s: %s", filepath, repr(os_error))
            return False
