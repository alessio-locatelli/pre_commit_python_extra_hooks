"""Detect and fix comments that are misplaced on closing bracket lines.

STYLE-001: Comments on closing bracket lines should be moved to the expression
line (inline if it fits within 88 chars, otherwise as a preceding comment).

Example:
    Bad:  result = func(arg)  # Comment on closing bracket
    Good: result = func(arg)  # Comment on same line as expression
    or:   # Comment before expression
          result = func(arg)
"""

import argparse
import functools
import logging
import re
import sys
import tokenize
from io import StringIO
from pathlib import Path
from typing import NamedTuple

from pre_commit_hooks._cache import CacheManager
from pre_commit_hooks._prefilter import git_grep_filter

logger = logging.getLogger("fix_misplaced_comment")

# Linter pragma patterns that should NEVER be moved
LINTER_PRAGMA_PATTERNS = [
    r"#\s*noqa",  # flake8, ruff
    r"#\s*type:\s*ignore",  # mypy, pyright
    r"#\s*pragma:",  # coverage, general pragma
    r"#\s*pylint:",  # pylint
    r"#\s*pyright:",  # pyright
    r"#\s*mypy:",  # mypy
    r"#\s*flake8:",  # flake8
    r"#\s*ruff:",  # ruff
    r"#\s*bandit:",  # bandit
    r"#\s*nosec",  # bandit
    r"#\s*isort:",  # isort
]

# Pre-compile regex patterns for performance (optimization)
_COMPILED_LINTER_PATTERNS = {re.compile(p) for p in LINTER_PRAGMA_PATTERNS}


@functools.cache
def is_linter_pragma(comment_text: str) -> bool:
    """
    Args:
        comment_text: The comment text (including # character)

    Returns:
        True if the comment matches any linter pragma pattern
    """
    # Use pre-compiled patterns (performance optimization)
    return any(pattern.search(comment_text) for pattern in _COMPILED_LINTER_PATTERNS)


def is_bracket_only_line(
    tokens: list[tokenize.TokenInfo], bracket_token_idx: int
) -> bool:
    """
    Args:
        tokens: List of all tokens in the file
        bracket_token_idx: Index of the bracket token to check

    Returns:
        True if the line contains only closing brackets (and whitespace)
    """
    bracket_token = tokens[bracket_token_idx]
    line_num = bracket_token.start[0]

    # Find all tokens on this line
    line_tokens = [t for t in tokens if t.start[0] == line_num]

    # Filter out NEWLINE, NL, INDENT, DEDENT, COMMENT, ENCODING
    code_tokens = [
        t
        for t in line_tokens
        if t.type
        not in (
            tokenize.NEWLINE,
            tokenize.NL,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.COMMENT,
            tokenize.ENCODING,
        )
    ]

    # Check if all code tokens are closing brackets
    return all(t.type == tokenize.OP and t.string in ")}]" for t in code_tokens)


class MisplacedComment(NamedTuple):
    """Represents a comment that needs to be moved."""

    line_number: int
    comment_text: str
    closing_bracket_line: int
    bracket_char: str


def check_file(filename: str) -> list[tuple[int, str]]:
    """
    Args:
        filename: Path to Python file to check

    Returns:
        List of (line_number, message) tuples for violations
    """
    try:
        with tokenize.open(filename) as f:
            source = f.read()
    except (SyntaxError, UnicodeDecodeError) as error:
        logger.warning("File: %s, error: %s", filename, repr(error))
        return []

    try:
        tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    except tokenize.TokenError as token_error:
        logger.warning("File: %s, error: %s", filename, repr(token_error))
        return []

    violations = []

    # Scan tokens for closing brackets followed by comments on same line
    for i, token in enumerate(tokens):
        # Check if this is a closing bracket operator
        if token.type == tokenize.OP and token.string in ")}]":
            # Look for a comment on the same line
            for j in range(i + 1, len(tokens)):
                next_token = tokens[j]

                # Stop if we hit a newline/NEWLINE/NL on a different line
                if next_token.start[0] > token.start[0]:
                    break

                # Found a comment on same line as closing bracket
                if next_token.type == tokenize.COMMENT:
                    # Skip linter pragma comments - they should NEVER be moved
                    if is_linter_pragma(next_token.string):
                        break

                    # Check if this is a bracket-only line using token analysis
                    if is_bracket_only_line(tokens, i):
                        violations.append(
                            (
                                token.start[0],
                                f"Comment on line {next_token.start[0]} should not be "
                                f"on closing bracket line",
                            )
                        )
                    break

    return violations


def fix_file(filename: str) -> None:
    """
    Args:
        filename: Path to Python file to fix
    """
    try:
        with tokenize.open(filename) as f:
            source = f.read()
            encoding = f.encoding
    except (SyntaxError, UnicodeDecodeError) as error:
        logger.warning("File: %s, error: %s", filename, repr(error))
        return

    try:
        tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    except tokenize.TokenError as token_error:
        logger.warning("File: %s, error: %s", filename, repr(token_error))
        return

    # Find misplaced comments and move them
    lines = source.splitlines(keepends=True)
    new_lines = lines[:]

    # Track which bracket lines have already been processed (to avoid duplicates)
    processed_lines: set[int] = set()

    # Track which comments to move
    for i, token in enumerate(tokens):
        if token.type == tokenize.OP and token.string in ")}]":
            # Look for comment on same line
            for j in range(i + 1, len(tokens)):
                next_token = tokens[j]

                if next_token.start[0] > token.start[0]:
                    break

                if next_token.type == tokenize.COMMENT:
                    # Skip linter pragma comments - they should NEVER be moved
                    if is_linter_pragma(next_token.string):
                        break

                    # Check if this is a bracket-only line using token analysis
                    if is_bracket_only_line(tokens, i):
                        bracket_line_num = token.start[0]

                        # Skip if already processed (multiple brackets)
                        if bracket_line_num in processed_lines:
                            break

                        processed_lines.add(bracket_line_num)
                        comment_text = next_token.string
                        bracket_line_idx = bracket_line_num - 1
                        prev_line_idx = bracket_line_idx - 1

                        if prev_line_idx >= 0:
                            # Try to place comment on previous line
                            prev_line = new_lines[prev_line_idx].rstrip()
                            # Get indentation from previous line
                            indent = len(new_lines[prev_line_idx]) - len(
                                new_lines[prev_line_idx].lstrip()
                            )

                            # Calculate if inline comment would exceed 88 chars
                            potential_inline = f"{prev_line}  {comment_text}"
                            if len(potential_inline) <= 88:
                                # Place inline on previous line
                                new_lines[prev_line_idx] = (
                                    prev_line + f"  {comment_text}\n"
                                )
                            else:
                                # Place as preceding comment
                                new_lines[prev_line_idx] = (
                                    " " * indent
                                    + f"{comment_text}\n"
                                    + prev_line
                                    + "\n"
                                )

                            # Remove comment from bracket line
                            new_lines[bracket_line_idx] = (
                                new_lines[bracket_line_idx][
                                    : next_token.start[1]
                                ].rstrip()
                                + "\n"
                            )
                    break

    # Write back with preserved encoding
    try:
        with open(filename, "w", encoding=encoding, newline="") as f:
            f.writelines(new_lines)
    except OSError as os_error:
        logger.error("Failed to write %s. Error: %s", filename, repr(os_error))


def main(argv: list[str] | None = None) -> int:
    """
    Args:
        argv: Command line arguments (if None, uses sys.argv[1:])

    Returns:
        Exit code (0 if no violations, 1 if violations found/fixed)
    """
    parser = argparse.ArgumentParser(
        description="Fix comments misplaced on closing brackets"
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check")
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix violations"
    )

    args = parser.parse_args(argv)

    if not args.filenames:
        return 0

    # Pre-filter: only process files with comments
    candidates = git_grep_filter(args.filenames, "#", fixed_string=True)
    if not candidates:
        return 0

    # Initialize cache
    cache = CacheManager(hook_name="fix-misplaced-comments")

    exit_code = 0
    for filename in candidates:
        filepath = Path(filename)

        # Try cache first (skip cache in --fix mode since file will be modified)
        violations = None
        if not args.fix:
            cached = cache.get_cached_result(filepath, "fix-misplaced-comments")
            if cached is not None:
                violations = [
                    tuple(v) for v in cached.get("violations", [])
                ]  # Convert from list

        # If cache miss, run check
        if violations is None:
            violations = check_file(filename)

            # Cache result (only if not in --fix mode)
            if not args.fix:
                cache.set_cached_result(
                    filepath,
                    "fix-misplaced-comments",
                    {"violations": [list(v) for v in violations]},
                )

        if violations:
            if args.fix:
                fix_file(filename)
                print(f"Fixed: {filename}", file=sys.stderr)
            else:
                for line_num, message in violations:
                    print(
                        f"{filename}:{line_num}: STYLE-001: {message}", file=sys.stderr
                    )
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
