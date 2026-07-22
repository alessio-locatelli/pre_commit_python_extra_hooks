from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from pre_commit_hooks.ast_checks.redundant_assignment import RedundantAssignmentCheck
from pre_commit_hooks.ast_checks.redundant_assignment.semantic import AggressivenessLevel

if TYPE_CHECKING:
    from pre_commit_hooks.ast_checks._base import Violation


def _check(
    source: str,
    path: str = "test.py",
    level: AggressivenessLevel = AggressivenessLevel.CONSERVATIVE,
) -> list[Violation]:
    return RedundantAssignmentCheck(level=level).check(Path(path), ast.parse(source), source)
