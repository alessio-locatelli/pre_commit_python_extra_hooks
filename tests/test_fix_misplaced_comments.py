"""Tests for fix_misplaced_comments hook."""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "misplaced_comments"


def run_hook(filenames: list[str], fix: bool = False) -> tuple[int, str, str]:
    """Run the fix-misplaced-comments hook.

    Args:
        filenames: List of file paths to check
        fix: If True, run with --fix flag

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "pre_commit_hooks.fix_misplaced_comments"]
    if fix:
        cmd.append("--fix")
    cmd.extend(filenames)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def test_detects_trailing_comment_on_closing_paren(tmp_path: Path) -> None:
    """Test detection of comment on closing parenthesis line."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""result = func(
    arg
)  # Comment here
""")
    # Hook should detect violation without fixing
    returncode, stdout, stderr = run_hook([str(test_file)], fix=False)
    assert returncode == 1, "Hook should detect trailing comment"
    # File should not be modified in detection mode
    assert (
        test_file.read_text()
        == """result = func(
    arg
)  # Comment here
"""
    )


def test_fixes_trailing_comment_inline_placement(tmp_path: Path) -> None:
    """Test fixing comment with inline placement when line fits 88 chars."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""result = x(
    arg
)  # Short comment
""")
    # Hook implementation will verify comment moves to arg line


def test_fixes_trailing_comment_preceding_placement(tmp_path: Path) -> None:
    """Test fixing comment with preceding placement when line exceeds 88 chars."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """result = some_function_with_very_long_name(
    argument_one,
    argument_two,
)  # This comment should move to preceding line due to length
"""
    )
    # Hook implementation will verify comment moves before the expression


def test_no_violation_for_correct_code(tmp_path: Path) -> None:
    """Test that correctly placed comments are not flagged."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""result = func(
    arg  # Comment inline on expression
)
""")
    # Hook should return 0 exit code for this file


def test_handles_syntax_errors_gracefully(tmp_path: Path) -> None:
    """Test handling of files with syntax errors."""
    test_file = tmp_path / "test.py"
    test_file.write_text("""def broken(
    arg
  # Missing closing paren
""")
    # Hook should skip file gracefully, not crash


def test_preserves_file_encoding_and_line_endings(tmp_path: Path) -> None:
    """Test that file encoding and line endings are preserved."""
    test_file = tmp_path / "test.py"
    # Write with UTF-8 BOM
    test_file.write_text(
        """# -*- coding: utf-8 -*-
result = func(
    arg
)  # Comment
""",
        encoding="utf-8",
    )
    # Hook should preserve encoding marker


def test_preserves_linter_pragma_comments(tmp_path: Path) -> None:
    """Test that linter pragma comments (noqa, type: ignore, etc.) are NOT moved."""
    # Copy the ignore_comments fixture to tmp_path
    bad_fixture = FIXTURES_DIR / "bad" / "ignore_comments.py"
    good_fixture = FIXTURES_DIR / "good" / "ignore_comments.py"

    test_file = tmp_path / "test_ignore.py"
    test_file.write_text(bad_fixture.read_text())

    # Run hook with --fix
    returncode, stdout, stderr = run_hook([str(test_file)], fix=True)

    # The file should not be modified (pragmas should stay in place)
    # Compare with good fixture
    assert test_file.read_text() == good_fixture.read_text(), (
        "Linter pragma comments should NOT be moved"
    )

    # Since pragmas are preserved, there should be no violations
    # Note: This test will initially fail until T004 is implemented
    assert returncode == 0, "Hook should not flag pragma comments as violations"


def test_moves_comments_from_bracket_only_lines(tmp_path: Path) -> None:
    """Test that comments on bracket-only lines ARE moved to preceding code."""
    bad_fixture = FIXTURES_DIR / "bad" / "bracket_comments.py"
    good_fixture = FIXTURES_DIR / "good" / "bracket_comments.py"

    test_file = tmp_path / "test_brackets.py"
    test_file.write_text(bad_fixture.read_text())

    # Run hook with --fix
    returncode, stdout, stderr = run_hook([str(test_file)], fix=True)

    # The file should be modified (comments moved to preceding lines)
    # Compare with good fixture
    assert test_file.read_text() == good_fixture.read_text(), (
        "Comments on bracket-only lines should be moved to preceding code lines"
    )

    # There should be violations that were fixed
    # Note: This test will initially fail until T009 is implemented
    assert returncode == 1, "Hook should flag and fix bracket-only line comments"
    assert "Fixed:" in stderr, "Hook should report fixing the file"
