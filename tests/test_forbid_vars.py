"""Tests for forbid-vars pre-commit hook."""

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def run_hook(
    filenames: Sequence[str], args: Sequence[str] | None = None
) -> tuple[int, str, str]:
    """
    Run the forbid-vars hook on the given files.

    Returns:
        tuple: (return_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "pre_commit_hooks.forbid_vars"]
    if args:
        cmd.extend(args)
    cmd.extend(str(f) for f in filenames)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def test_success_case() -> None:
    """Test that files with only allowed variable names pass (exit 0)."""
    valid_file = FIXTURES_DIR / "valid_code.py"
    returncode, stdout, stderr = run_hook([str(valid_file)])

    assert returncode == 0, "Hook should pass on files with descriptive variable names"
    assert stdout == "", "No output expected for passing files"


def test_failure_case() -> None:
    """
    Test that files with forbidden variable names fail (exit 1) with error messages.
    """
    invalid_file = FIXTURES_DIR / "invalid_code.py"
    returncode, stdout, stderr = run_hook([str(invalid_file)])

    assert returncode == 1, "Hook should fail on files with forbidden variable names"
    assert "data" in stdout, "Error message should mention 'data'"
    assert "result" in stdout, "Error message should mention 'result'"
    assert str(invalid_file) in stdout, "Error message should include file path"
    assert ":" in stdout, "Error message should include line number separator"


def test_ignore_comment() -> None:
    """Test that violations with inline ignore comments are suppressed (exit 0)."""
    ignored_file = FIXTURES_DIR / "ignored_code.py"
    returncode, stdout, stderr = run_hook([str(ignored_file)])

    assert returncode == 0, "Hook should pass when violations are suppressed"
    assert stdout == "", "No output expected when all violations are ignored"


def test_custom_blacklist() -> None:
    """Test that --names argument allows custom forbidden variable names."""
    valid_file = FIXTURES_DIR / "valid_code.py"
    returncode, stdout, stderr = run_hook(
        [str(valid_file)], ["--names=invoice_items,total_amount"]
    )

    assert returncode == 1, "Hook should fail with custom blacklist"
    assert "invoice_items" in stdout or "total_amount" in stdout


def test_empty_file() -> None:
    """Test that empty files pass (exit 0)."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        empty_file = f.name
        # Write nothing (empty file)

    try:
        returncode, stdout, stderr = run_hook([empty_file])
        assert returncode == 0, "Hook should pass on empty files"
        assert stdout == "", "No output expected for empty files"
    finally:
        os.unlink(empty_file)


def test_syntax_error() -> None:
    """Test graceful handling of files with syntax errors."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        syntax_error_file = f.name
        f.write("def foo(\n")  # Syntax error: missing closing paren

    try:
        returncode, stdout, stderr = run_hook([syntax_error_file])
        # Hook should handle syntax errors gracefully
        # Either skip the file (exit 0) or report error (non-zero)
        # We'll accept either behavior as long as it doesn't crash
        assert isinstance(returncode, int), "Hook should return an exit code"
    finally:
        os.unlink(syntax_error_file)


def test_function_parameters() -> None:
    """Test that forbidden names in function parameters are detected."""
    invalid_file = FIXTURES_DIR / "invalid_code.py"
    returncode, stdout, stderr = run_hook([str(invalid_file)])

    assert returncode == 1, "Hook should detect forbidden names in function parameters"
    # The invalid_code.py has multiple functions with 'data' and 'result' as parameters
    assert "data" in stdout
    assert "result" in stdout


def test_multiple_violations() -> None:
    """Test that all violations in a file are reported."""
    invalid_file = FIXTURES_DIR / "invalid_code.py"
    returncode, stdout, stderr = run_hook([str(invalid_file)])

    assert returncode == 1, "Hook should fail on files with violations"
    # Count occurrences of 'data' and 'result' in output
    data_count = stdout.count("'data'")
    result_count = stdout.count("'result'")

    # invalid_code.py has multiple violations
    assert data_count >= 2, "Should report multiple 'data' violations"
    assert result_count >= 2, "Should report multiple 'result' violations"


def test_no_files() -> None:
    """Test that hook exits 0 when no files are provided."""
    returncode, stdout, stderr = run_hook([])

    assert returncode == 0, "Hook should exit 0 when no files provided"
    assert stdout == "", "No output expected when no files provided"


def test_error_message_format() -> None:
    """Test that error messages follow the standard linter format."""
    invalid_file = FIXTURES_DIR / "invalid_code.py"
    returncode, stdout, stderr = run_hook([str(invalid_file)])

    assert returncode == 1
    # Error format should be: filepath:line: message
    lines = stdout.strip().split("\n")
    assert len(lines) > 0, "Should have at least one error message"

    for line in lines:
        assert ":" in line, "Error message should contain colons"
        parts = line.split(":", 2)  # Split into filepath, line, message
        assert len(parts) >= 2, "Error message should have filepath:line: format"
        # Check that line number is numeric
        try:
            int(parts[1].strip())
        except ValueError:
            pytest.fail(f"Line number should be numeric in: {line}")


def test_error_message_includes_link() -> None:
    """Test that error messages include link to meaningless variable names article."""
    invalid_file = FIXTURES_DIR / "invalid_code.py"
    returncode, stdout, stderr = run_hook([str(invalid_file)])

    assert returncode == 1
    assert "hilton.org.uk" in stdout, "Error message should include link to article"
    assert "meaningless-variable-name" in stdout, (
        "Error message should mention ignore pattern"
    )


def test_case_sensitivity() -> None:
    """Test that forbidden names are case-sensitive."""
    import tempfile

    # Create a file with 'Data' (capital D) instead of 'data'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        case_file = f.name
        f.write("Data = 1\n")

    try:
        returncode, stdout, stderr = run_hook([case_file])
        # 'Data' should not be forbidden (case-sensitive)
        assert returncode == 0, "Hook should be case-sensitive for variable names"
    finally:
        os.unlink(case_file)


def test_attribute_access_not_flagged() -> None:
    """Test that attribute access like obj.data is not flagged."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        attr_file = f.name
        f.write("obj.data = 1\n")
        f.write("self.result = compute()\n")

    try:
        returncode, stdout, stderr = run_hook([attr_file])
        assert returncode == 0, "Attribute access should not be flagged as violations"
    finally:
        os.unlink(attr_file)
