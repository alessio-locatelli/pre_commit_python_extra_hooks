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

from pre_commit_hooks._cache import CacheManager
from pre_commit_hooks._prefilter import git_grep_filter

from .analysis import GET_PREFIX, Suggestion, process_file
from .autofix import apply_fix, should_autofix

ERROR_CODE = "NAMING-001"


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

    # Pre-filter: only process files with "def get_" pattern
    candidate_files = git_grep_filter(
        args.filenames, f"def {GET_PREFIX}", fixed_string=True
    )

    if not candidate_files:
        # No candidate files found
        return 0

    # Initialize cache
    cache = CacheManager(hook_name="validate-function-name")

    # Process each file and collect suggestions
    all_suggestions: list[Suggestion] = []
    for filename in candidate_files:
        filepath = Path(filename)

        # Try cache first (skip cache in --fix mode since file may be modified)
        suggestions = None
        if not args.fix:
            cached = cache.get_cached_result(filepath, "validate-function-name")
            if cached is not None:
                # Deserialize suggestions from cache
                suggestions = [
                    Suggestion(
                        path=Path(s["path"]),
                        func_name=s["func_name"],
                        lineno=s["lineno"],
                        suggested_name=s["suggested_name"],
                        reason=s["reason"],
                    )
                    for s in cached.get("suggestions", [])
                ]

        # If cache miss, run analysis
        if suggestions is None:
            suggestions = process_file(filepath)

            # Cache result (only if not in --fix mode)
            if not args.fix:
                # Serialize suggestions for caching
                cache.set_cached_result(
                    filepath,
                    "validate-function-name",
                    {
                        "suggestions": [
                            {
                                "path": str(s.path),
                                "func_name": s.func_name,
                                "lineno": s.lineno,
                                "suggested_name": s.suggested_name,
                                "reason": s.reason,
                            }
                            for s in suggestions
                        ]
                    },
                )

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


# Check class for grouped linter integration
import ast  # noqa: E402
import logging  # noqa: E402
from typing import TYPE_CHECKING  # noqa: E402

if TYPE_CHECKING:
    from pre_commit_hooks.ast_checks._base import Violation

logger_check = logging.getLogger("validate_function_name_check")


def _make_check_class() -> type:
    """Create the check class (delayed import to avoid circular dependencies)."""
    from .. import register_check
    from .._base import Violation

    @register_check
    class ValidateFunctionNameCheck:
        """Check for get_* functions and suggest better names."""

        @property
        def check_id(self) -> str:
            """Return check identifier."""
            return "validate-function-name"

        @property
        def error_code(self) -> str:
            """Return error code."""
            return ERROR_CODE

        def get_prefilter_pattern(self) -> str | None:
            """Return pre-filter pattern."""
            return "def get_"

        def check(
            self, filepath: Path, tree: ast.Module, source: str
        ) -> list[Violation]:
            """Run check and return violations.

            Args:
                filepath: Path to file
                tree: Parsed AST tree
                source: Source code

            Returns:
                List of violations
            """
            # Use existing analysis module
            suggestions = process_file(filepath)

            # Convert Suggestion objects to Violation objects
            violations = []
            for suggestion in suggestions:
                message = (
                    f"Function '{suggestion.func_name}' should be renamed to "
                    f"'{suggestion.suggested_name}' ({suggestion.reason})"
                )

                violations.append(
                    Violation(
                        check_id=self.check_id,
                        error_code=self.error_code,
                        line=suggestion.lineno,
                        col=0,
                        message=message,
                        fixable=True,  # May be fixable based on complexity
                        fix_data={
                            "suggestion": suggestion,  # Store original for autofix
                        },
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
            """Apply fixes for function naming violations.

            Args:
                filepath: Path to file
                violations: Violations to fix
                source: Source code
                tree: Parsed AST tree

            Returns:
                True if fixes were applied successfully
            """
            if not violations:
                return False

            applied_any = False

            for violation in violations:
                if not violation.fix_data:
                    continue

                suggestion = violation.fix_data.get("suggestion")
                if not suggestion:
                    continue

                # Check if safe to autofix
                if should_autofix(filepath, suggestion):
                    try:
                        if apply_fix(filepath, suggestion):
                            applied_any = True
                            # Mark as fixed
                            violation.fix_data["fixed"] = True
                    except Exception as fix_error:  # noqa: BLE001
                        logger_check.error(
                            "Failed to apply fix for %s in %s: %s",
                            suggestion.func_name,
                            filepath,
                            repr(fix_error),
                        )

            return applied_any

    return ValidateFunctionNameCheck


# Register the check when this module is imported
_make_check_class()
