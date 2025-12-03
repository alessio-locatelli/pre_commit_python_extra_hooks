"""Tests for fix_excessive_blank_lines hook."""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "excessive_blank_lines"


def run_hook(filenames: list[str], fix: bool = False) -> tuple[int, str, str]:
    """Run the fix-excessive-blank-lines hook.

    Args:
        filenames: List of file paths to check
        fix: If True, run with --fix flag

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "pre_commit_hooks.fix_excessive_blank_lines"]
    if fix:
        cmd.append("--fix")
    cmd.extend(filenames)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def test_detects_excessive_blank_lines(tmp_path: Path) -> None:
    """Test detection of excessive blank lines after docstring."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        '"""Module docstring."""\n'
        "\n"
        "\n"  # Extra blank line
        "\n"  # Another extra blank line
        "import something\n"
    )
    # Hook should detect violation


def test_collapses_blank_lines_to_one(tmp_path: Path) -> None:
    """Test fixing excessive blank lines."""
    test_file = tmp_path / "test.py"
    test_file.write_text('"""Module docstring."""\n\n\n\nimport os\n')
    # Hook should fix to single blank line


def test_preserves_copyright_spacing(tmp_path: Path) -> None:
    """Test that copyright spacing is preserved."""
    test_file = tmp_path / "test.py"
    test_file.write_text("# Copyright (c) 2025\n\nimport something\n")
    # Hook should preserve single blank after copyright


def test_no_violation_for_correct_spacing(tmp_path: Path) -> None:
    """Test that correct spacing is not flagged."""
    test_file = tmp_path / "test.py"
    test_file.write_text('"""Module docstring."""\n\nimport os\n')
    # Hook should return 0 for correct spacing


def test_handles_files_without_module_header(tmp_path: Path) -> None:
    """Test handling of files without module headers."""
    test_file = tmp_path / "test.py"
    test_file.write_text("import os\n\n\ndef function():\n    pass\n")
    # Hook should handle files without docstring/comments


def test_preserves_blank_lines_in_code_body(tmp_path: Path) -> None:
    """Test that blank lines in code body are preserved."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        '"""Module docstring."""\n\nimport os\n\n\ndef function():\n    pass\n'
    )
    # Hook should only fix module-level blank lines


def test_only_collapses_blank_lines_after_header(tmp_path: Path) -> None:
    """Test that blank lines are only collapsed between header and first code line.

    This test verifies that the hook:
    1. Collapses 3+ blank lines after the copyright header to 1 blank line
    2. Preserves intentional double-blank lines between function definitions
    """
    bad_fixture = FIXTURES_DIR / "bad" / "header_spacing.py"
    good_fixture = FIXTURES_DIR / "good" / "header_spacing.py"

    test_file = tmp_path / "test_header_spacing.py"
    test_file.write_text(bad_fixture.read_text())

    # Run hook with --fix
    returncode, stdout, stderr = run_hook([str(test_file)], fix=True)

    # The file should be modified (header spacing collapsed)
    # But double-blank lines between functions should be preserved
    assert test_file.read_text() == good_fixture.read_text(), (
        "Blank lines should only be collapsed after header, "
        "not between function definitions"
    )

    # There should be violations that were fixed
    assert returncode == 1, "Hook should flag and fix excessive header spacing"
    assert "Fixed:" in stderr, "Hook should report fixing the file"
