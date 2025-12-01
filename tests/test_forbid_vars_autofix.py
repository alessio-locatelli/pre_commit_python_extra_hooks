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
