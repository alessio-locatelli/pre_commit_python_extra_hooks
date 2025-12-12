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
import logging
import sys
from pathlib import Path

from pre_commit_hooks._cache import CacheManager

logger = logging.getLogger("fix_excessive_blank_lines")


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
    except (OSError, UnicodeDecodeError) as error:
        logger.warning("File: %s, error: %s", filename, repr(error))
        return []

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


def fix_file(filename: str) -> None:
    """Fix excessive blank lines in file.

    Args:
        filename: Path to Python file
    """
    try:
        with open(filename, encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines(keepends=True)
    except (OSError, UnicodeDecodeError) as error:
        logger.warning("File: %s, error: %s", filename, repr(error))
        return

    if not lines:
        return

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

    for i in range(last_header_line, len(lines)):
        line = lines[i]
        is_blank = line.strip() == ""

        if is_blank:
            blank_count += 1
            if not found_first_code_line:
                # Before first code line: collapse consecutive blank lines to 1
                if blank_count == 1:
                    new_lines.append(line)
            else:
                # After first code line: preserve all blank lines
                new_lines.append(line)
        else:
            # Non-blank line
            blank_count = 0
            found_first_code_line = True
            new_lines.append(line)

    # Write back
    try:
        with open(filename, "w", encoding="utf-8", newline="") as f:
            f.writelines(new_lines)
    except OSError as os_error:
        logger.error("Failed to write %s. Error: %s", filename, repr(os_error))


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 if no violations, 1 if violations found/fixed)
    """
    parser = argparse.ArgumentParser(
        description="Fix excessive blank lines after module headers"
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check")
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix violations"
    )

    args = parser.parse_args(argv)

    if not args.filenames:
        return 0

    # Initialize cache
    cache = CacheManager(hook_name="fix-excessive-blank-lines")

    exit_code = 0
    for filename in args.filenames:
        filepath = Path(filename)

        # Try cache first (skip cache in --fix mode since file will be modified)
        violations = None
        if not args.fix:
            cached = cache.get_cached_result(filepath, "fix-excessive-blank-lines")
            if cached is not None:
                violations = [
                    tuple(v) for v in cached.get("violations", [])
                ]  # Convert from list

        # If cache miss, run check
        if violations is None:
            violations = check_file(filename)

            # Cache result (only if not in --fix mode)
            if not args.fix:
                # Convert tuples to lists for JSON serialization
                cache.set_cached_result(
                    filepath,
                    "fix-excessive-blank-lines",
                    {"violations": [list(v) for v in violations]},
                )

        if violations:
            if args.fix:
                fix_file(filename)
                print(f"Fixed: {filename}", file=sys.stderr)
            else:
                for line_num, message in violations:
                    print(
                        f"{filename}:{line_num}: STYLE-002: {message}", file=sys.stderr
                    )
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
