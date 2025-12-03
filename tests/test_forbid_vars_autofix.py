"""Tests for the autofix feature of the forbid-vars pre-commit hook."""

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
AUTOFIXABLE_DIR = FIXTURES_DIR / "autofixable"


def run_hook(
    cwd: Path,
    filenames: Sequence[str],
    args: Sequence[str] | None = None,
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

    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=cwd)
    return result.returncode, result.stdout, result.stderr


PYPROJECT_TOML_HTTP_ENABLED = """
[tool.forbid-vars.autofix]
enabled = ["http"]
"""

PYPROJECT_TOML_FILE_ENABLED = """
[tool.forbid-vars.autofix]
enabled = ["file", "http"]
"""


def setup_test_env(
    tmp_path: Path, config_content: str, bad_files: dict[str, str]
) -> None:
    """Setup a temporary test environment."""
    (tmp_path / "pyproject.toml").write_text(config_content)

    for name, content in bad_files.items():
        (tmp_path / name).write_text(content)


def test_suggest_mode_http(tmp_path: Path) -> None:
    """Test that suggestions are printed for the http category."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "http.py").read_text()
    setup_test_env(tmp_path, PYPROJECT_TOML_HTTP_ENABLED, {"http.py": bad_file_content})

    returncode, stdout, stderr = run_hook(tmp_path, ["http.py"])

    assert returncode == 1
    assert "Forbidden variable name 'result' found." in stdout
    assert "Consider renaming to 'response'." in stdout
    assert "Forbidden variable name 'data' found." in stdout
    assert "Consider renaming to 'payload'." in stdout


def test_fix_mode_http(tmp_path: Path) -> None:
    """Test that --fix flag corrects http violations."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "http.py").read_text()
    good_file_content = (AUTOFIXABLE_DIR / "good" / "http.py").read_text()
    setup_test_env(tmp_path, PYPROJECT_TOML_HTTP_ENABLED, {"http.py": bad_file_content})

    returncode, stdout, stderr = run_hook(tmp_path, ["http.py"], ["--fix"])

    assert returncode == 1, "Hook should return 1 when fixes are applied"

    fixed_content = (tmp_path / "http.py").read_text()
    assert fixed_content == good_file_content


def test_suggest_mode_file_open(tmp_path: Path) -> None:
    """Test suggestions for file open."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "file_open.py").read_text()
    setup_test_env(
        tmp_path, PYPROJECT_TOML_FILE_ENABLED, {"file_open.py": bad_file_content}
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["file_open.py"])

    assert returncode == 1
    assert "Consider renaming to 'file_handle'" in stdout
    assert "Consider renaming to 'parsed_data'" in stdout


def test_fix_mode_file_open(tmp_path: Path) -> None:
    """Test that --fix flag corrects file open violations."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "file_open.py").read_text()
    good_file_content = (AUTOFIXABLE_DIR / "good" / "file_open.py").read_text()
    setup_test_env(
        tmp_path, PYPROJECT_TOML_FILE_ENABLED, {"file_open.py": bad_file_content}
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["file_open.py"], ["--fix"])

    assert returncode == 1
    fixed_content = (tmp_path / "file_open.py").read_text()
    assert fixed_content == good_file_content


def test_suggest_mode_file_read_text(tmp_path: Path) -> None:
    """Test suggestions for file read_text."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "file_read_text.py").read_text()
    setup_test_env(
        tmp_path,
        PYPROJECT_TOML_FILE_ENABLED,
        {"file_read_text.py": bad_file_content},
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["file_read_text.py"])

    assert returncode == 1
    assert "Consider renaming to 'file_content'" in stdout


def test_fix_mode_file_read_text(tmp_path: Path) -> None:
    """Test that --fix flag corrects file read_text violations."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "file_read_text.py").read_text()
    good_file_content = (AUTOFIXABLE_DIR / "good" / "file_read_text.py").read_text()
    setup_test_env(
        tmp_path,
        PYPROJECT_TOML_FILE_ENABLED,
        {"file_read_text.py": bad_file_content},
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["file_read_text.py"], ["--fix"])

    assert returncode == 1
    fixed_content = (tmp_path / "file_read_text.py").read_text()
    assert fixed_content == good_file_content


def test_fix_mode_name_collision(tmp_path: Path) -> None:
    """Test that name collisions are handled correctly."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "name_collision.py").read_text()
    good_file_content = (AUTOFIXABLE_DIR / "good" / "name_collision.py").read_text()
    setup_test_env(
        tmp_path,
        PYPROJECT_TOML_HTTP_ENABLED,
        {"name_collision.py": bad_file_content},
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["name_collision.py"], ["--fix"])

    assert returncode == 1
    fixed_content = (tmp_path / "name_collision.py").read_text()
    assert fixed_content == good_file_content


PYPROJECT_TOML_HTTP_DISABLED = """
[tool.forbid-vars.autofix]
enabled = ["file"]
"""


def test_disabled_category(tmp_path: Path) -> None:
    """Test that disabled categories are not autofixed."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "http.py").read_text()
    setup_test_env(
        tmp_path, PYPROJECT_TOML_HTTP_DISABLED, {"http.py": bad_file_content}
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["http.py"], ["--fix"])

    # The hook should still fail because of the forbidden names,
    # but it should not apply any fixes.
    assert returncode == 1

    # Check that no suggestions were made
    assert "Applied fix" not in stdout

    # Check that the file was not modified
    fixed_content = (tmp_path / "http.py").read_text()
    assert fixed_content == bad_file_content


PYPROJECT_TOML_CUSTOM_PATTERN = """
[tool.forbid-vars.autofix]
enabled = ["custom"]

[[tool.forbid-vars.autofix.patterns]]
category = "custom"
regex = "get_my_data"
name = "my_data"
"""


def test_custom_pattern(tmp_path: Path) -> None:
    """Test that custom patterns are correctly applied."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "custom.py").read_text()
    good_file_content = (AUTOFIXABLE_DIR / "good" / "custom.py").read_text()
    setup_test_env(
        tmp_path, PYPROJECT_TOML_CUSTOM_PATTERN, {"custom.py": bad_file_content}
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["custom.py"], ["--fix"])

    assert returncode == 1
    fixed_content = (tmp_path / "custom.py").read_text()
    assert fixed_content == good_file_content


def test_bug1_no_redundant_suffix(tmp_path: Path) -> None:
    """Test Bug 1 fix: no redundant suffix when no conflict exists."""
    bad_path = AUTOFIXABLE_DIR / "bad" / "bug1_redundant_suffix.py"
    good_path = AUTOFIXABLE_DIR / "good" / "bug1_redundant_suffix.py"
    bad_file_content = bad_path.read_text()
    good_file_content = good_path.read_text()

    setup_test_env(
        tmp_path,
        PYPROJECT_TOML_HTTP_ENABLED,
        {"bug1_redundant_suffix.py": bad_file_content},
    )

    returncode, stdout, stderr = run_hook(
        tmp_path, ["bug1_redundant_suffix.py"], ["--fix"]
    )

    # Hook should return 1 (violations found and fixed)
    assert returncode == 1

    # Verify the fix
    fixed_content = (tmp_path / "bug1_redundant_suffix.py").read_text()
    assert fixed_content == good_file_content

    # Ensure no redundant suffix was added in the code (not in docstrings)
    lines = fixed_content.split("\n")
    # Find the line with the assignment and check it doesn't have _2
    assignment_lines = [line for line in lines if "= request.get()" in line]
    assert len(assignment_lines) == 1
    assert "response_2" not in assignment_lines[0]
    assert "response = request.get()" in fixed_content


def test_bug2_no_function_param_rename(tmp_path: Path) -> None:
    """Test Bug 2: Function parameters should not be renamed."""
    bad_path = AUTOFIXABLE_DIR / "bad" / "bug2_function_param.py"
    good_path = AUTOFIXABLE_DIR / "good" / "bug2_function_param.py"
    bad_file_content = bad_path.read_text()
    good_file_content = good_path.read_text()

    setup_test_env(
        tmp_path,
        PYPROJECT_TOML_HTTP_ENABLED,
        {"bug2_function_param.py": bad_file_content},
    )

    returncode, stdout, stderr = run_hook(
        tmp_path, ["bug2_function_param.py"], ["--fix"]
    )

    # Violation should be detected but NOT fixed (function params)
    assert returncode == 1

    # File should be unchanged
    fixed_content = (tmp_path / "bug2_function_param.py").read_text()
    assert fixed_content == good_file_content
    assert "def delay_received(data: bytes)" in fixed_content


def test_bug2_no_keyword_arg_rename(tmp_path: Path) -> None:
    """Test Bug 2: Keyword argument names should not be renamed."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "bug2_keyword_arg.py").read_text()
    good_file_content = (AUTOFIXABLE_DIR / "good" / "bug2_keyword_arg.py").read_text()

    setup_test_env(
        tmp_path, PYPROJECT_TOML_HTTP_ENABLED, {"bug2_keyword_arg.py": bad_file_content}
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["bug2_keyword_arg.py"], ["--fix"])

    assert returncode == 1

    fixed_content = (tmp_path / "bug2_keyword_arg.py").read_text()
    assert fixed_content == good_file_content
    # Keyword arg name should NOT change
    assert "data=" in fixed_content
    # Variable is not fixed because no autofix pattern matches
    assert 'data = "compressed"' in fixed_content


def test_bug2_no_attribute_rename(tmp_path: Path) -> None:
    """Test Bug 2: Object attributes should not be renamed."""
    bad_file_content = (AUTOFIXABLE_DIR / "bad" / "bug2_attribute.py").read_text()
    good_file_content = (AUTOFIXABLE_DIR / "good" / "bug2_attribute.py").read_text()

    setup_test_env(
        tmp_path, PYPROJECT_TOML_HTTP_ENABLED, {"bug2_attribute.py": bad_file_content}
    )

    returncode, stdout, stderr = run_hook(tmp_path, ["bug2_attribute.py"], ["--fix"])

    assert returncode == 1

    fixed_content = (tmp_path / "bug2_attribute.py").read_text()
    assert fixed_content == good_file_content
    # Attribute access should NOT change
    assert "msg.result" in fixed_content
    # Variable should be renamed
    assert "response = api.get()" in fixed_content


def test_bug2_no_string_literal_rename(tmp_path: Path) -> None:
    """Test Bug 2: String literal content should not be modified."""
    bad_path = AUTOFIXABLE_DIR / "bad" / "bug2_string_literal.py"
    good_path = AUTOFIXABLE_DIR / "good" / "bug2_string_literal.py"
    bad_file_content = bad_path.read_text()
    good_file_content = good_path.read_text()

    setup_test_env(
        tmp_path,
        PYPROJECT_TOML_HTTP_ENABLED,
        {"bug2_string_literal.py": bad_file_content},
    )

    returncode, stdout, stderr = run_hook(
        tmp_path, ["bug2_string_literal.py"], ["--fix"]
    )

    assert returncode == 1

    fixed_content = (tmp_path / "bug2_string_literal.py").read_text()
    assert fixed_content == good_file_content
    # String content should NOT change
    assert '"some data here"' in fixed_content
    assert '"data is important"' in fixed_content
    # Variable is not fixed because no autofix pattern matches
    assert 'data = "test"' in fixed_content
