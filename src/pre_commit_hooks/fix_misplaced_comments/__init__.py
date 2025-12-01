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
import sys
import tokenize
from io import StringIO
from typing import NamedTuple


class MisplacedComment(NamedTuple):
    """Represents a comment that needs to be moved."""

    line_number: int
    comment_text: str
    closing_bracket_line: int
    bracket_char: str


def check_file(filename: str) -> list[tuple[int, str]]:
    """Check file for misplaced comments.

    Args:
        filename: Path to Python file to check

    Returns:
        List of (line_number, message) tuples for violations
    """
    try:
        with tokenize.open(filename) as f:
            source = f.read()
    except (SyntaxError, UnicodeDecodeError):
        return []

    try:
        tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    except tokenize.TokenError:
        return []

    violations = []
    lines = source.splitlines(keepends=True)

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
                    # Check if closing bracket is alone on its line
                    # (only whitespace before it on that line)
                    line_content = lines[token.start[0] - 1]
                    before_bracket = line_content[: token.start[1]].strip()

                    if not before_bracket or before_bracket.endswith(("(", "[", "{")):
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
    """Fix misplaced comments in file.

    Args:
        filename: Path to Python file to fix
    """
    try:
        with tokenize.open(filename) as f:
            source = f.read()
            encoding = f.encoding
    except (SyntaxError, UnicodeDecodeError):
        return

    try:
        tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    except tokenize.TokenError:
        return

    # Find misplaced comments and move them
    lines = source.splitlines(keepends=True)
    new_lines = lines[:]

    # Track which comments to move
    for i, token in enumerate(tokens):
        if token.type == tokenize.OP and token.string in ")}]":
            # Look for comment on same line
            for j in range(i + 1, len(tokens)):
                next_token = tokens[j]

                if next_token.start[0] > token.start[0]:
                    break

                if next_token.type == tokenize.COMMENT:
                    line_content = lines[token.start[0] - 1]
                    before_bracket = line_content[: token.start[1]].strip()

                    if not before_bracket or before_bracket.endswith(("(", "[", "{")):
                        comment_text = next_token.string
                        bracket_line_idx = token.start[0] - 1
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
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the hook.

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

    exit_code = 0
    for filename in args.filenames:
        violations = check_file(filename)
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
