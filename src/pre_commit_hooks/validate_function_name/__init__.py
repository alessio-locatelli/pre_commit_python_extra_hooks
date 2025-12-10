"""validate_function_name - Detect get_* functions and suggest better names.

NAMING-001: Functions with get_ prefix should use more descriptive names
based on their behavior (e.g., load_, fetch_, calculate_, is_, iter_).

This hook detects functions prefixed with `get_` and suggests more specific
names based on behavioral analysis:

- Boolean returns → is_*
- Disk I/O → load_*/save_*
- Network I/O → fetch_*/send_*
- Generators → iter_*
- Aggregation → calculate_*
- Parsing → parse_*
- Searching → find_*
- Validation → validate_*
- Collection → extract_*
- Object creation → create_*
- Mutation → update_*

Usage:
    validate_function_name [--fix] <files>

Options:
    --fix    Auto-fix safe violations (small, simple functions only)

Suppression:
    Add inline comment to suppress: # naming: ignore

Example:
    def get_users() -> list[User]:  # naming: ignore
        return User.objects.all()
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .analysis import GET_PREFIX, Suggestion, process_file
from .autofix import apply_fix, should_autofix

ERROR_CODE = "NAMING-001"


def _should_scan_file(filepath: Path) -> bool:
    """Quick pre-filter to check if file might contain get_* functions.

    Args:
        filepath: Path to Python file

    Returns:
        True if file should be scanned (contains "def get_")
    """
    try:
        content = filepath.read_text(encoding="utf8")
        return f"def {GET_PREFIX}" in content
    except (OSError, UnicodeDecodeError):
        return False


def _format_violation(
    suggestion: Suggestion, fixed: bool = False, skipped_reason: str | None = None
) -> str:
    """Format a violation message.

    Args:
        suggestion: The naming suggestion
        fixed: Whether the violation was auto-fixed
        skipped_reason: Reason autofix was skipped (if applicable)

    Returns:
        Formatted violation message
    """
    prefix = "[FIXED]" if fixed else "[SUGGESTION]"
    base_msg = (
        f"{suggestion.path}:{suggestion.lineno}: {ERROR_CODE}: "
        f"{prefix} Function '{suggestion.func_name}' should be renamed to "
        f"'{suggestion.suggested_name}' ({suggestion.reason})"
    )

    if skipped_reason:
        base_msg += f" - {skipped_reason}"

    return base_msg


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for validate_function_name hook.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code: 0 if no violations, 1 if violations found
    """
    parser = argparse.ArgumentParser(
        prog="validate_function_name",
        description="Detect get_* functions and suggest better names based on behavior",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Python files to check",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix safe violations (small, simple functions only)",
    )

    args = parser.parse_args(argv)

    if not args.filenames:
        # No files to process
        return 0

    # Convert to Path objects
    files = [Path(f) for f in args.filenames]

    # Pre-filter files for performance
    candidate_files = [f for f in files if _should_scan_file(f)]

    if not candidate_files:
        # No candidate files found
        return 0

    # Process each file and collect suggestions
    all_suggestions: list[Suggestion] = []
    for filepath in candidate_files:
        suggestions = process_file(filepath)
        all_suggestions.extend(suggestions)

    if not all_suggestions:
        # No violations found
        return 0

    # Track violations and fixes
    exit_code = 1  # At least one violation found
    fixed_count = 0
    skipped_count = 0

    # Process suggestions
    for suggestion in all_suggestions:
        if args.fix:
            # Check if safe to auto-fix
            if should_autofix(suggestion.path, suggestion):
                # Apply the fix
                if apply_fix(suggestion.path, suggestion):
                    print(_format_violation(suggestion, fixed=True))
                    fixed_count += 1
                else:
                    # Fix failed for some reason
                    print(
                        _format_violation(
                            suggestion,
                            fixed=False,
                            skipped_reason="auto-fix failed",
                        )
                    )
                    skipped_count += 1
            else:
                # Not safe to auto-fix
                print(
                    _format_violation(
                        suggestion,
                        fixed=False,
                        skipped_reason=(
                            "auto-fix skipped (function too complex or large)"
                        ),
                    )
                )
                skipped_count += 1
        else:
            # Just report the suggestion
            print(_format_violation(suggestion, fixed=False))

    # Summary for --fix mode
    if args.fix and (fixed_count > 0 or skipped_count > 0):
        print(
            f"\nSummary: {fixed_count} auto-fixed, "
            f"{skipped_count} skipped (manual review needed)"
        )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
