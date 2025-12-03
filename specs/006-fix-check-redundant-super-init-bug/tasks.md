# Tasks: Fix check-redundant-super-init False-Positive Bug

**Feature**: Fix check-redundant-super-init False-Positive Bug
**Branch**: `006-fix-check-redundant-super-init-bug`
**Date**: 2025-12-03

---

## Implementation Strategy

This is a focused bug fix for the `check-redundant-super-init` hook that currently reports false-positives when `**kwargs` is forwarded through an inheritance chain where only the deepest ancestor accepts `**kwargs`. The fix involves modifying the `_parent_accepts_args()` method to recursively traverse the inheritance chain.

**MVP Scope**: Complete the bug fix implementation and validation in a single phase.

---

## Phase 1: Setup & Analysis

Understand the bug and current implementation before making changes.

**Phase Goal**: Establish baseline understanding of the bug and implementation details.

**Independent Test Criteria**:
- Confirm the aiohttp code example reproduces the false-positive with current implementation
- Document the inheritance chain traversal needed to resolve it

### Tasks

- [X] T001 Read the current implementation in `src/pre_commit_hooks/check_redundant_super_init/__init__.py` to understand the SuperInitChecker class and _parent_accepts_args() method logic
- [X] T002 Review the test file `tests/test_check_redundant_super_init.py` to understand existing test coverage and test patterns
- [X] T003 Create a test fixture with the aiohttp-style inheritance chain (HTTPException → HTTPError → HTTPClientError → HTTPRequestEntityTooLarge) in `tests/fixtures/` directory
- [X] T004 Verify that the current implementation reports a false-positive on the aiohttp code example

---

## Phase 2: Implementation & Testing

Implement the inheritance chain traversal fix and validate it.

**Phase Goal**: Fix the bug by modifying `_parent_accepts_args()` to recursively check inheritance chains.

**Independent Test Criteria**:
- The aiohttp code example no longer reports false-positive
- All existing tests still pass
- New test case validates the inheritance chain traversal behavior
- Code passes ruff and mypy checks

### Tasks

- [X] T005 [P] Modify the `_parent_accepts_args()` method in `src/pre_commit_hooks/check_redundant_super_init/__init__.py` to recursively traverse the inheritance chain instead of only checking direct parents
- [X] T006 [P] Add a new test case `test_no_violation_with_inheritance_chain()` in `tests/test_check_redundant_super_init.py` that validates the aiohttp inheritance pattern is no longer flagged as false-positive
- [X] T007 Run existing tests with `uv run pytest tests/test_check_redundant_super_init.py` to ensure no regressions
- [X] T008 Run linting with `uv run ruff check --fix src/pre_commit_hooks/check_redundant_super_init/` to ensure code quality
- [X] T009 Run type checking with `uv run mypy src/pre_commit_hooks/check_redundant_super_init/` to ensure type safety
- [X] T010 Manually test the hook against the aiohttp code example to confirm the false-positive is resolved

---

## Phase 3: Integration & Polish

Ensure the fix integrates correctly with the full test suite and project standards.

**Phase Goal**: Validate the fix across the entire project and prepare for merge.

**Independent Test Criteria**:
- All project tests pass
- All linting and type checking passes
- Code follows project conventions

### Tasks

- [X] T011 Run full test suite with `uv run pytest` to ensure no impact on other hooks or tests
- [X] T012 Run full project linting with `uv run ruff check --fix .` to ensure consistency across codebase
- [X] T013 Run full project type checking with `uv run mypy src/` to ensure no type regressions
- [X] T014 Format code with `npx prettier . --write --cache` to ensure consistent formatting
- [X] T015 Format pyproject.toml with `taplo fmt pyproject.toml` to ensure config consistency

---

## Dependencies & Parallelization

### Execution Order

1. **Phase 1 (Sequential)**: Must complete before proceeding to implementation
   - T001 → T002 → T003 → T004 (sequential, each builds on previous understanding)

2. **Phase 2 (Mostly Parallel)**:
   - T005 and T006 can run in parallel [P] (different files, no dependencies)
   - T007, T008, T009 must follow T005 and T006 completion
   - T010 must follow T009

3. **Phase 3 (Sequential)**:
   - T011 → T012 → T013 → T014 → T015 (validation must be in order)

### Parallel Execution Example

```
Phase 1:  T001 → T002 → T003 → T004
          ↓
Phase 2:  [T005 | T006] → T007 → T008 → T009 → T010
          ↓
Phase 3:  T011 → T012 → T013 → T014 → T015
```

---

## Success Metrics

- **All tasks completed**: 15/15 tasks marked complete
- **Test coverage**: No regression in existing tests, new test case added
- **Code quality**: All linting and type checks pass
- **False-positive fixed**: Aiohttp code example no longer flagged as error

---

## Notes

- The bug fix is isolated to a single method (`_parent_accepts_args()`)
- The fix should not impact other hooks or functionality
- All project conventions (ruff, mypy, prettier, taplo) must be followed
- The implementation should maintain backward compatibility with existing bug detection
