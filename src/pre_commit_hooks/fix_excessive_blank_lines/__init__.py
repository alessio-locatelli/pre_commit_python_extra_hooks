"""Detect and fix excessive blank lines after module headers.

STYLE-002: Collapse 2+ consecutive blank lines after module headers (copyright,
docstring, or comments) to a single blank line. Preserves copyright spacing.

Example:
    Bad:  '''Module docstring'''


          import os

    Good: '''Module docstring'''

          import os
"""

import argparse
import sys


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


def check_file(filename: str) -> list[tuple[int, str]]:
    """Check file for excessive blank lines.

    Args:
        filename: Path to Python file

    Returns:
        List of (line_number, message) tuples
    """
    try:
        with open(filename, encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return []

    if not lines:
        return []

    violations = []
    header_end = find_module_header_end(lines)

    blank_count = 0
    start_blank = None

    for i in range(header_end, len(lines)):
        line = lines[i]
        if line.strip() == "":
            if blank_count == 0:
                start_blank = i
            blank_count += 1
        else:
            # Non-blank line found
            if blank_count >= 2:
                violations.append(
                    (
                        start_blank + 1,
                        f"Excessive blank lines ({blank_count}) should be collapsed to 1",
                    )
                )
            blank_count = 0
            start_blank = None

    return violations


def fix_file(filename: str) -> None:
    """Fix excessive blank lines in file.

    Args:
        filename: Path to Python file
    """
    try:
        with open(filename, encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines(keepends=True)
    except (OSError, UnicodeDecodeError):
        return

    if not lines:
        return

    header_end = find_module_header_end(lines)
    new_lines = lines[:header_end]

    blank_count = 0
    for i in range(header_end, len(lines)):
        line = lines[i]
        is_blank = line.strip() == ""

        if is_blank:
            blank_count += 1
            if blank_count == 1:
                # Keep first blank line after header
                new_lines.append(line)
        else:
            # Non-blank line
            blank_count = 0
            new_lines.append(line)

    # Write back
    try:
        with open(filename, "w", encoding="utf-8", newline="") as f:
            f.writelines(new_lines)
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 if no violations, 1 if violations found/fixed)
    """
    parser = argparse.ArgumentParser(description="Fix excessive blank lines after module headers")
    parser.add_argument("filenames", nargs="*", help="Filenames to check")
    parser.add_argument("--fix", action="store_true", help="Automatically fix violations")

    args = parser.parse_args(argv)

    exit_code = 0
    for filename in args.filenames:
        violations = check_file(filename)
        if violations:
            if args.fix:
                fix_file(filename)
                print(f"Fixed: {filename}", file=sys.stderr)
            else:
                for line_num, message in violations:
                    print(f"{filename}:{line_num}: STYLE-002: {message}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
