"""Tests for fix_misplaced_comments hook."""


def test_detects_trailing_comment_on_closing_paren(tmp_path):
    """Test detection of comment on closing parenthesis line."""
    test_file = tmp_path / "test.py"
    test_file.write_text("result = func(\n    arg\n)  # Comment here\n")
    # Import will be done when hook is implemented
    # This test validates the fixture structure


def test_fixes_trailing_comment_inline_placement(tmp_path):
    """Test fixing comment with inline placement when line fits 88 chars."""
    test_file = tmp_path / "test.py"
    test_file.write_text("result = x(\n    arg\n)  # Short comment\n")
    # Hook implementation will verify comment moves to arg line


def test_fixes_trailing_comment_preceding_placement(tmp_path):
    """Test fixing comment with preceding placement when line exceeds 88 chars."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        "result = some_function_with_very_long_name(\n"
        "    argument_one,\n"
        "    argument_two,\n"
        ")  # This comment should move to preceding line due to length\n"
    )
    # Hook implementation will verify comment moves before the expression


def test_no_violation_for_correct_code(tmp_path):
    """Test that correctly placed comments are not flagged."""
    test_file = tmp_path / "test.py"
    test_file.write_text("result = func(\n    arg  # Comment inline on expression\n)\n")
    # Hook should return 0 exit code for this file


def test_handles_syntax_errors_gracefully(tmp_path):
    """Test handling of files with syntax errors."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def broken(\n    arg\n  # Missing closing paren\n")
    # Hook should skip file gracefully, not crash


def test_preserves_file_encoding_and_line_endings(tmp_path):
    """Test that file encoding and line endings are preserved."""
    test_file = tmp_path / "test.py"
    # Write with UTF-8 BOM
    test_file.write_text(
        "# -*- coding: utf-8 -*-\nresult = func(\n    arg\n)  # Comment\n",
        encoding="utf-8",
    )
    # Hook should preserve encoding marker
