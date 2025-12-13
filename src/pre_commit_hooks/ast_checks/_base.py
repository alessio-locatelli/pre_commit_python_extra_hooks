"""Base protocols and data structures for AST-based checks."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass
class Violation:
    """Represents a single violation found by a check.

    Attributes:
        check_id: Unique identifier for the check (e.g., "forbid-vars")
        error_code: Error code for the violation (e.g., "TRI001")
        line: Line number where the violation occurs
        col: Column offset where the violation occurs
        message: Human-readable description of the violation
        fixable: Whether the violation can be auto-fixed
        fix_data: Check-specific data needed for applying the fix
    """

    check_id: str
    error_code: str
    line: int
    col: int
    message: str
    fixable: bool
    fix_data: dict[str, Any] | None = None


class ASTCheck(Protocol):
    """Protocol that all AST-based checks must implement.

    This protocol defines the interface for pluggable AST checks in the
    grouped linter. Each check should be independent and stateless with
    respect to file processing.
    """

    @property
    def check_id(self) -> str:
        """Unique identifier for this check.

        Examples: "forbid-vars", "redundant-super-init", "validate-function-name"

        Returns:
            Check identifier string
        """
        ...

    @property
    def error_code(self) -> str:
        """Error code prefix for violations from this check.

        Examples: "TRI001", "TRI002", "TRI003"

        Returns:
            Error code string
        """
        ...

    def get_prefilter_pattern(self) -> str | None:
        """Pattern for git grep pre-filtering.

        Return a fixed string pattern that identifies files that might
        contain violations for this check. If None, all files will be
        checked (no pre-filtering).

        Returns:
            Pattern string for git grep, or None for no filtering

        Examples:
            - "def get_" for validate-function-name
            - "super().__init__" for redundant-super-init
            - None for excessive-blank-lines (check all files)
        """
        ...

    def check(self, filepath: Path, tree: ast.Module, source: str) -> list[Violation]:
        """Run check on a file and return violations.

        Args:
            filepath: Path to the file being checked
            tree: Parsed AST tree of the file
            source: Original source code as string

        Returns:
            List of violations found in the file
        """
        ...

    def fix(
        self,
        filepath: Path,
        violations: list[Violation],
        source: str,
        tree: ast.Module,
    ) -> bool:
        """Apply fixes for the given violations.

        Args:
            filepath: Path to the file to fix
            violations: List of violations to fix (all from this check)
            source: Original source code as string
            tree: Parsed AST tree of the file

        Returns:
            True if fixes were successfully applied, False otherwise
        """
        ...
