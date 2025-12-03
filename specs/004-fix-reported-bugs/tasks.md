# Tasks for 004-fix-reported-bugs

This file outlines the tasks to fix the bugs reported in `bugs_report.md`.

## Phase 1: Setup

There are no specific setup tasks for this feature, as it involves modifying an existing project.

## Phase 2: Foundational Tasks

There are no foundational tasks required.

## Phase 3: User Story 1 - `fix-misplaced-comments` Ignore Comments

**Goal**: The hook should not move "ignore" comments (e.g., `# noqa`, `# type: ignore`).
**Independent Test Criteria**: The hook correctly identifies and skips ignore comments, leaving them in their original positions.

- [X] T001 [US1] Create a new test fixture `tests/fixtures/misplaced_comments/bad/ignore_comments.py` with various linter pragma comments that should NOT be moved (# noqa, # type: ignore, # pragma: no cover, # pylint:, # mypy:, etc.). Include edge case: multiple pragmas on same line. See bugs_report.md BUG 1 for examples.
- [X] T002 [P] [US1] Create the corresponding good fixture `tests/fixtures/misplaced_comments/good/ignore_comments.py` showing the correct, untouched code.
- [X] T003 [US1] Add a new test case to `tests/test_fix_misplaced_comments.py` that uses the `ignore_comments` fixture and fails.
- [X] T004 [US1] In `src/pre_commit_hooks/fix_misplaced_comments/__init__.py`, add a `LINTER_PRAGMA_PATTERNS` module constant (list of regex patterns) and an `is_linter_pragma(comment_text: str) -> bool` helper function. Update both `check_file()` and `fix_file()` to skip comments matching these patterns. See research.md for the complete pattern list.
- [X] T005 [US1] Run the test for `ignore_comments` to ensure it passes.

## Phase 4: User Story 2 - `fix-misplaced-comments` Closing Bracket Comments

**Goal**: The hook should correctly handle comments on lines that contain only closing brackets.
**Independent Test Criteria**: The hook correctly identifies and moves comments from lines that only contain closing brackets.

- [X] T006 [P] [US2] Create a new test fixture `tests/fixtures/misplaced_comments/bad/bracket_comments.py` with comments on bracket-only lines (lines containing only `)`, `}`, `]` and whitespace). Include edge case: mixed closing brackets like `)])`. The comment should be on the bracket line (will be moved by the fix). See bugs_report.md BUG 2 for the exact example pattern.
- [X] T007 [P] [US2] Create the corresponding good fixture `tests/fixtures/misplaced_comments/good/bracket_comments.py` showing the comment in the correct position.
- [X] T008 [US2] Add a new test case to `tests/test_fix_misplaced_comments.py` for the `bracket_comments` fixture, which should initially fail.
- [X] T009 [US2] In `src/pre_commit_hooks/fix_misplaced_comments/__init__.py`, update the logic using the `tokenize` module to correctly identify and move comments on bracket-only lines.
- [X] T010 [US2] Run the test for `bracket_comments` to ensure it passes.

## Phase 5: User Story 3 - `fix-excessive-blank-lines` Top-Level Comments

**Goal**: The hook should only collapse excessive blank lines between a top-level comment block and the first line of code.
**Independent Test Criteria**: The hook correctly identifies the region between the top-level comment and the first code statement and collapses blank lines only in that region.

- [X] T011 [P] [US3] Create a new test fixture `tests/fixtures/excessive_blank_lines/bad/header_spacing.py` with a copyright/license comment header followed by 3+ blank lines before the first import statement. Also include intentional double-blank lines between function definitions (these should NOT be modified). Include edge case: file with no header (blank lines should not be touched).
- [X] T012 [P] [US3] Create the corresponding good fixture `tests/fixtures/excessive_blank_lines/good/header_spacing.py` with the correct spacing.
- [X] T013 [US3] Add a new test case to `tests/test_fix_excessive_blank_lines.py` for the `header_spacing` fixture, which should initially fail.
- [X] T014 [US3] In `src/pre_commit_hooks/fix_excessive_blank_lines/__init__.py`, modify the logic to only apply to the region between the file header and the first code statement.
- [X] T015 [US3] Run the test for `header_spacing` to ensure it passes.

## Final Phase: Polish & Cross-Cutting Concerns

- [X] T016 Run `uv run ruff check --fix .` and `uv run ruff format .` to ensure code quality.
- [X] T017 Run `uv run mypy src/` to check for type errors.
- [X] T018 Run `uv run pytest` to ensure all tests pass.

## Dependencies

- US1, US2, and US3 are independent and can be worked on in parallel.

## Parallel Execution

- Tasks marked with `[P]` can be executed in parallel within their respective user stories. For example, `T001` and `T002` can be done at the same time.

## Implementation Strategy

The strategy is to address each bug as a separate user story. Each story involves creating a failing test case that reproduces the bug, implementing the fix, and then ensuring the test passes.
