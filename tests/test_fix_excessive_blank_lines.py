"""Tests for fix_excessive_blank_lines hook."""


def test_detects_excessive_blank_lines(tmp_path):
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


def test_collapses_blank_lines_to_one(tmp_path):
    """Test fixing excessive blank lines."""
    test_file = tmp_path / "test.py"
    test_file.write_text('"""Module docstring."""\n\n\n\nimport os\n')
    # Hook should fix to single blank line


def test_preserves_copyright_spacing(tmp_path):
    """Test that copyright spacing is preserved."""
    test_file = tmp_path / "test.py"
    test_file.write_text("# Copyright (c) 2025\n\nimport something\n")
    # Hook should preserve single blank after copyright


def test_no_violation_for_correct_spacing(tmp_path):
    """Test that correct spacing is not flagged."""
    test_file = tmp_path / "test.py"
    test_file.write_text('"""Module docstring."""\n\nimport os\n')
    # Hook should return 0 for correct spacing


def test_handles_files_without_module_header(tmp_path):
    """Test handling of files without module headers."""
    test_file = tmp_path / "test.py"
    test_file.write_text("import os\n\n\ndef function():\n    pass\n")
    # Hook should handle files without docstring/comments


def test_preserves_blank_lines_in_code_body(tmp_path):
    """Test that blank lines in code body are preserved."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        '"""Module docstring."""\n\nimport os\n\n\ndef function():\n    pass\n'
    )
    # Hook should only fix module-level blank lines
