"""Tests for CheckOrchestrator (ast_checks/__init__.py)."""

from __future__ import annotations

from pathlib import Path

from pre_commit_hooks.ast_checks import CheckOrchestrator
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
