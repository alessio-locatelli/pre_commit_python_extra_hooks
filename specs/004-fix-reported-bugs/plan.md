# Implementation Plan: Fix Reported Bugs in Pre-commit Hooks

**Branch**: `004-fix-reported-bugs` | **Date**: 2025-12-01 | **Spec**: [./spec.md](./spec.md)
**Input**: Feature specification from `/var/home/sam/projects/pre_commit_extra_hooks/specs/004-fix-reported-bugs/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan addresses three critical bugs in the pre-commit hooks library:
1. The `fix-misplaced-comments` hook incorrectly moves linter ignore comments, breaking their functionality
2. The `fix-misplaced-comments` hook mishandles comments on bracket-only lines
3. The `fix-excessive-blank-lines` hook over-aggressively collapses blank lines throughout files instead of only targeting the header region

The technical approach involves using Python's tokenize module for precise token-level analysis, implementing a blacklist of linter pragmas, and scoping the blank line logic to only the file header region.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: pytest, ruff, mypy (all dev dependencies, no runtime dependencies)
**Storage**: N/A (operates on files in-place)
**Testing**: pytest with fixture-based test cases
**Target Platform**: Python environment
**Project Type**: Single project (pre-commit hooks library)
**Performance Goals**: Hook execution time <100ms per file (typical for pre-commit hooks)
**Constraints**: No third-party runtime dependencies (per constitution), must maintain backward compatibility
**Scale/Scope**: Bug fixes affecting 2 existing hooks, approximately 5-10 files modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: Simplicity and Appropriate Technology ✅
- **Status**: PASS
- **Evidence**: Bug fixes will be implemented in Python 3.13+ using only standard library modules (tokenize, ast, re). No third-party dependencies will be added.
- **Implementation**: Use tokenize module for bracket detection, regex for pragma matching

### Principle 2: Performance as a Feature ✅
- **Status**: PASS
- **Evidence**: Bug fixes optimize the existing logic to be more precise (only processing relevant regions), which should maintain or improve performance. The tokenize module is part of the standard library and efficient for this use case.
- **Note**: Performance will be validated during testing phase

### Principle 3: Rigorous Testing ✅
- **Status**: PASS
- **Evidence**: Spec requires comprehensive test coverage (SC-005) including:
  - Test fixtures for each bug scenario
  - Edge case coverage (5 identified edge cases)
  - All three user stories have explicit acceptance scenarios
- **Implementation**: pytest fixtures will be created for each bug scenario

### Principle 4: User-Centric Configuration ✅
- **Status**: PASS
- **Evidence**: FR-009 explicitly requires backward compatibility. No changes to `.pre-commit-config.yaml` interface or hook behavior (only bug fixes).
- **Implementation**: Existing hook entry points and CLI interfaces remain unchanged

**GATE RESULT**: ✅ All principles satisfied, proceeding to Phase 0 research.

---

### Post-Design Constitution Re-check ✅

After completing Phase 1 design (research.md, data-model.md, contracts/, quickstart.md), re-evaluating constitution compliance:

#### Principle 1: Simplicity and Appropriate Technology ✅
- **Status**: PASS (Confirmed)
- **Design Evidence**:
  - research.md confirms use of only standard library modules: `re`, `tokenize`
  - No third-party dependencies introduced
  - Implementation approaches are straightforward pattern matching and token analysis
- **Complexity Assessment**: Low - all solutions use existing standard library capabilities

#### Principle 2: Performance as a Feature ✅
- **Status**: PASS (Confirmed)
- **Design Evidence**:
  - Linter pragma check: O(1) regex match per comment (minimal overhead)
  - Bracket-only detection: Already using tokenize module, no additional I/O
  - Blank line scope: Reduces work by limiting to header region (performance improvement)
- **Performance Assessment**: No degradation expected; header-scoping should improve performance

#### Principle 3: Rigorous Testing ✅
- **Status**: PASS (Confirmed)
- **Design Evidence**:
  - 6 new test fixtures planned (3 bugs × 2 fixture files each)
  - Edge cases explicitly documented in research.md
  - Each bug has specific test strategy defined
- **Test Coverage Assessment**: Comprehensive - all scenarios and edge cases covered

#### Principle 4: User-Centric Configuration ✅
- **Status**: PASS (Confirmed)
- **Design Evidence**:
  - contracts/cli-interface.md confirms zero breaking changes
  - quickstart.md shows seamless upgrade path (just update version)
  - All existing `.pre-commit-config.yaml` configurations work unchanged
- **Compatibility Assessment**: 100% backward compatible

**POST-DESIGN GATE RESULT**: ✅ All principles remain satisfied after detailed design. Proceeding to Phase 2 (tasks generation via `/speckit.tasks`).

## Project Structure

### Documentation (this feature)

```text
specs/004-fix-reported-bugs/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── pre_commit_hooks/
    ├── fix_excessive_blank_lines/
    │   ├── __init__.py
    │   └── __main__.py          # Will be modified for FR-005 to FR-008
    └── fix_misplaced_comments/
        ├── __init__.py
        └── __main__.py          # Will be modified for FR-001 to FR-004

tests/
├── fixtures/
│   ├── excessive_blank_lines/
│   │   ├── bad/
│   │   │   └── header_spacing.py     # NEW: Test for US3
│   │   └── good/
│   │       └── header_spacing.py     # NEW: Test for US3
│   └── misplaced_comments/
│       ├── bad/
│       │   ├── ignore_comments.py    # NEW: Test for US1
│       │   └── bracket_comments.py   # NEW: Test for US2
│       └── good/
│           ├── ignore_comments.py    # NEW: Test for US1
│           └── bracket_comments.py   # NEW: Test for US2
├── test_fix_excessive_blank_lines.py  # Will add new test cases
└── test_fix_misplaced_comments.py     # Will add new test cases
```

**Structure Decision**: The existing single-project structure is maintained. Bug fixes will modify the two affected hook implementations and add corresponding test fixtures. No architectural changes are required.

## Complexity Tracking

No violations to the constitution have been identified. All bug fixes align with existing principles.
