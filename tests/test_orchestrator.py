"""Tests for CheckOrchestrator (ast_checks/__init__.py)."""

from __future__ import annotations

from pathlib import Path

from pre_commit_hooks.ast_checks import CheckOrchestrator, load_checks
from pre_commit_hooks.ast_checks.forbid_vars import ForbidVarsCheck


def test_process_files_handles_utf8_bom(tmp_path: Path) -> None:
    """A UTF-8 BOM must not make the orchestrator silently skip the file.

    filepath.read_text(encoding="utf-8") decodes a leading BOM as a literal
    U+FEFF character, which ast.parse rejects as a syntax error — reading
    with utf-8-sig strips it transparently instead (and is identical to
    utf-8 for files without one).
    """
    filepath = tmp_path / "with_bom.py"
    filepath.write_bytes(b"\xef\xbb\xbfdata = 1\n")

    orchestrator = CheckOrchestrator(checks=[ForbidVarsCheck()])
    violations = orchestrator.process_files([str(filepath)])

    assert len(violations[str(filepath)]) == 1
    assert violations[str(filepath)][0].error_code == "TRI001"


def test_apply_fixes_handles_utf8_bom(tmp_path: Path) -> None:
    """The re-read before each check's fix() call must also strip a BOM."""
    filepath = tmp_path / "with_bom.py"
    filepath.write_bytes(b"\xef\xbb\xbfdata = requests.get(url)\n")

    orchestrator = CheckOrchestrator(checks=[ForbidVarsCheck()], fix_mode=True)
    violations = orchestrator.process_files([str(filepath)])
    fix_data = violations[str(filepath)][0].fix_data

    assert fix_data is not None
    assert fix_data["fixed"] is True
    assert filepath.read_text(encoding="utf-8") == "response = requests.get(url)\n"


def test_apply_fixes_recomputes_stale_positions(tmp_path: Path) -> None:
    """A later check's fix() must not use line numbers from before an earlier
    check's fix already rewrote the file in the same --fix run.

    excessive-blank-lines runs (and fixes) before redundant-assignment in
    ALL_CHECKS order. Collapsing the 3 blank lines after the module docstring
    down to 2 removes one line, shifting `x = "foo"`/`print(x)` up by one —
    so if redundant-assignment's fix() were handed the violation positions
    collected before that collapse, it would edit the wrong (now-shifted)
    lines and silently fail to inline `x`.
    """
    filepath = tmp_path / "stale_positions.py"
    filepath.write_text(
        '"""Module docstring."""\n'
        "\n\n\n"
        "def func_scope():\n"
        '    x = "foo"\n'
        "    print(x)\n"
    )

    checks = load_checks(enabled={"excessive-blank-lines", "redundant-assignment"})
    orchestrator = CheckOrchestrator(checks=checks, fix_mode=True)
    violations = orchestrator.process_files([str(filepath)])

    redundant_assignment_fixed = any(
        v.check_id == "redundant-assignment" and v.fix_data and v.fix_data.get("fixed")
        for v in violations[str(filepath)]
    )
    assert redundant_assignment_fixed

    result = filepath.read_text(encoding="utf-8")
    assert 'x = "foo"' not in result
    assert "print(" in result
    assert '"foo"' in result


AST_INVALID_SOURCE = 'result = func(\n    x\n)  # comment\n\n\nprint "invalid"\n'


def test_ast_requiring_check_still_skips_unparseable_file(tmp_path: Path) -> None:
    """Regression guard: an AST-invalid file must behave as it did before
    requires_ast existed when only AST-dependent checks are enabled.
    """
    filepath = tmp_path / "ast_invalid.py"
    filepath.write_text(AST_INVALID_SOURCE)

    checks = load_checks(enabled={"forbid-vars"})
    orchestrator = CheckOrchestrator(checks=checks)
    violations = orchestrator.process_files([str(filepath)])

    assert violations == {}


def test_tokenize_only_check_reports_on_ast_invalid_file(tmp_path: Path) -> None:
    """misplaced-comment (requires_ast=False) must still report its
    violation even though this file fails ast.parse() (Python 2 `print`
    statement).
    """
    filepath = tmp_path / "ast_invalid.py"
    filepath.write_text(AST_INVALID_SOURCE)

    checks = load_checks(enabled={"misplaced-comment"})
    orchestrator = CheckOrchestrator(checks=checks)
    violations = orchestrator.process_files([str(filepath)])

    assert len(violations[str(filepath)]) == 1
    assert violations[str(filepath)][0].error_code == "STYLE-001"


def test_tokenize_only_check_fixes_ast_invalid_file(tmp_path: Path) -> None:
    """--fix must move the misplaced comment even though the file remains
    ast.parse()-invalid throughout (the fix itself never depends on a tree).
    """
    filepath = tmp_path / "ast_invalid.py"
    filepath.write_text(AST_INVALID_SOURCE)

    checks = load_checks(enabled={"misplaced-comment"})
    orchestrator = CheckOrchestrator(checks=checks, fix_mode=True)
    violations = orchestrator.process_files([str(filepath)])

    assert violations[str(filepath)][0].fix_data == {"fixed": True}
    result = filepath.read_text(encoding="utf-8")
    assert "x  # comment" in result
    assert ")\n" in result
    assert 'print "invalid"' in result  # still Python-2-invalid, untouched
