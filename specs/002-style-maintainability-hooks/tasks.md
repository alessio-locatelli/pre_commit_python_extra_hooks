# Tasks: Style and Maintainability Pre-commit Hooks

**Input**: Design documents from `/specs/002-style-maintainability-hooks/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included - Constitution IV requires comprehensive testing for all hooks

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each hook.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Hooks located in: `src/pre_commit_hooks/`
- Tests located in: `tests/`
- Fixtures located in: `tests/fixtures/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for all three hooks

- [x] T001 Create directory structure: `src/pre_commit_hooks/`, `tests/fixtures/{misplaced_comments,excessive_blank_lines,redundant_super_init}/{good,bad}`
- [x] T002 [P] Create `src/pre_commit_hooks/__init__.py` with package initialization
- [x] T003 [P] Create empty hook skeleton files: `src/pre_commit_hooks/fix_misplaced_comments.py`, `src/pre_commit_hooks/fix_excessive_blank_lines.py`, `src/pre_commit_hooks/check_redundant_super_init.py`
- [x] T004 [P] Create empty test skeleton files: `tests/test_fix_misplaced_comments.py`, `tests/test_fix_excessive_blank_lines.py`, `tests/test_check_redundant_super_init.py`

---

## Phase 2: Foundational (No Blocking Prerequisites)

**Purpose**: These hooks have no shared infrastructure - each is completely independent

**Note**: This project has no foundational phase because:
- Each hook uses only Python stdlib (no shared dependencies to set up)
- Hooks are independent (no shared code between them)
- No database, authentication, or API infrastructure needed

**Checkpoint**: Setup complete - all three user stories can now proceed in parallel

---

## Phase 3: User Story 1 - Detect and Fix Misplaced Comments (Priority: P1) 🎯 MVP

**Goal**: Implement hook that detects trailing comments on closing brackets and automatically moves them to the correct line (inline or preceding)

**Independent Test**: Run `python -m pre_commit_hooks.fix_misplaced_comments --fix` on a Python file with trailing comments on closing brackets and verify comments are moved appropriately

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] [US1] Create good fixture: `tests/fixtures/misplaced_comments/good/inline_comment.py` with properly placed inline comments
- [ ] T006 [P] [US1] Create good fixture: `tests/fixtures/misplaced_comments/good/preceding_comment.py` with properly placed preceding comments
- [ ] T007 [P] [US1] Create bad fixture: `tests/fixtures/misplaced_comments/bad/trailing_on_paren.py` with comment on closing parenthesis line
- [ ] T008 [P] [US1] Create bad fixture: `tests/fixtures/misplaced_comments/bad/trailing_on_bracket.py` with comment on closing bracket line
- [ ] T009 [P] [US1] Create bad fixture: `tests/fixtures/misplaced_comments/bad/trailing_on_brace.py` with comment on closing brace line
- [ ] T010 [P] [US1] Write test in `tests/test_fix_misplaced_comments.py`: test_detects_trailing_comment_on_closing_paren (detection mode)
- [ ] T011 [P] [US1] Write test in `tests/test_fix_misplaced_comments.py`: test_fixes_trailing_comment_inline_placement (fix mode, short line)
- [ ] T012 [P] [US1] Write test in `tests/test_fix_misplaced_comments.py`: test_fixes_trailing_comment_preceding_placement (fix mode, long line)
- [ ] T013 [P] [US1] Write test in `tests/test_fix_misplaced_comments.py`: test_no_violation_for_correct_code (good fixtures)
- [ ] T014 [P] [US1] Write test in `tests/test_fix_misplaced_comments.py`: test_handles_syntax_errors_gracefully (edge case)
- [ ] T015 [P] [US1] Write test in `tests/test_fix_misplaced_comments.py`: test_preserves_file_encoding_and_line_endings (encoding preservation)

### Implementation for User Story 1

- [ ] T016 [US1] Implement CLI argument parsing in `src/pre_commit_hooks/fix_misplaced_comments.py`: argparse with filenames and --fix flag
- [ ] T017 [US1] Implement file tokenization logic in `src/pre_commit_hooks/fix_misplaced_comments.py`: use tokenize.generate_tokens() to parse file
- [ ] T018 [US1] Implement misplaced comment detection in `src/pre_commit_hooks/fix_misplaced_comments.py`: scan for OP tokens with closing brackets followed by COMMENT on same line
- [ ] T019 [US1] Implement comment placement decision logic in `src/pre_commit_hooks/fix_misplaced_comments.py`: determine inline vs preceding based on 88 char line length
- [ ] T020 [US1] Implement comment movement logic in `src/pre_commit_hooks/fix_misplaced_comments.py`: reconstruct token stream with comment moved to target line
- [ ] T021 [US1] Implement file writing with encoding preservation in `src/pre_commit_hooks/fix_misplaced_comments.py`: use tokenize.open() to preserve encoding
- [ ] T022 [US1] Implement main() entry point in `src/pre_commit_hooks/fix_misplaced_comments.py`: process multiple files, aggregate exit codes, handle errors
- [ ] T023 [US1] Add error handling for syntax errors in `src/pre_commit_hooks/fix_misplaced_comments.py`: catch SyntaxError, skip file, report to stderr
- [ ] T024 [US1] Add module docstring and inline comments in `src/pre_commit_hooks/fix_misplaced_comments.py`: explain tokenize logic and placement heuristics

**Checkpoint**: At this point, User Story 1 (fix-misplaced-comments hook) should be fully functional and testable independently. Run `pytest tests/test_fix_misplaced_comments.py` to verify.

---

## Phase 4: User Story 2 - Detect and Fix Excessive Blank Lines (Priority: P2)

**Goal**: Implement hook that detects 2+ consecutive blank lines after module headers and collapses them to a single blank line (preserving copyright spacing)

**Independent Test**: Run `python -m pre_commit_hooks.fix_excessive_blank_lines --fix` on a Python file with excessive blank lines after module docstring and verify they are collapsed to one

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T025 [P] [US2] Create good fixture: `tests/fixtures/excessive_blank_lines/good/single_blank_after_docstring.py` with correct spacing
- [ ] T026 [P] [US2] Create good fixture: `tests/fixtures/excessive_blank_lines/good/copyright_spacing.py` with copyright + 1 blank line
- [ ] T027 [P] [US2] Create bad fixture: `tests/fixtures/excessive_blank_lines/bad/triple_blank_after_docstring.py` with 3 blank lines
- [ ] T028 [P] [US2] Create bad fixture: `tests/fixtures/excessive_blank_lines/bad/double_blank_after_comment.py` with 2 blank lines after top comment
- [ ] T029 [P] [US2] Write test in `tests/test_fix_excessive_blank_lines.py`: test_detects_excessive_blank_lines (detection mode)
- [ ] T030 [P] [US2] Write test in `tests/test_fix_excessive_blank_lines.py`: test_collapses_blank_lines_to_one (fix mode)
- [ ] T031 [P] [US2] Write test in `tests/test_fix_excessive_blank_lines.py`: test_preserves_copyright_spacing (copyright + 1 blank)
- [ ] T032 [P] [US2] Write test in `tests/test_fix_excessive_blank_lines.py`: test_no_violation_for_correct_spacing (good fixtures)
- [ ] T033 [P] [US2] Write test in `tests/test_fix_excessive_blank_lines.py`: test_handles_files_without_module_header (edge case)
- [ ] T034 [P] [US2] Write test in `tests/test_fix_excessive_blank_lines.py`: test_preserves_blank_lines_in_code_body (only affects module header area)

### Implementation for User Story 2

- [ ] T035 [US2] Implement CLI argument parsing in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: argparse with filenames and --fix flag
- [ ] T036 [US2] Implement module header detection in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: find end of shebang/encoding/docstring/comments
- [ ] T037 [US2] Implement copyright comment detection in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: regex for "# Copyright", "# (c)", "# ©"
- [ ] T038 [US2] Implement blank line counting state machine in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: track consecutive blank lines after header
- [ ] T039 [US2] Implement blank line collapsing logic in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: replace 2+ blank lines with 1
- [ ] T040 [US2] Implement file reading and writing in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: preserve encoding and line endings
- [ ] T041 [US2] Implement main() entry point in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: process multiple files, aggregate exit codes
- [ ] T042 [US2] Add error handling and edge case logic in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: empty files, files without headers
- [ ] T043 [US2] Add module docstring and inline comments in `src/pre_commit_hooks/fix_excessive_blank_lines.py`: explain state machine and copyright logic

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Run `pytest tests/test_fix_excessive_blank_lines.py` to verify US2.

---

## Phase 5: User Story 3 - Detect Redundant Super Init Kwargs (Priority: P3)

**Goal**: Implement hook that detects when a class forwards **kwargs to a parent __init__ that accepts no arguments (detection-only, no auto-fix)

**Independent Test**: Run `python -m pre_commit_hooks.check_redundant_super_init` on a Python file with redundant **kwargs forwarding and verify violation is detected

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T044 [P] [US3] Create good fixture: `tests/fixtures/redundant_super_init/good/matching_signatures.py` with proper signature matching
- [ ] T045 [P] [US3] Create good fixture: `tests/fixtures/redundant_super_init/good/parent_accepts_kwargs.py` with parent that accepts **kwargs
- [ ] T046 [P] [US3] Create bad fixture: `tests/fixtures/redundant_super_init/bad/redundant_kwargs_forwarding.py` with child forwarding to parent()
- [ ] T047 [P] [US3] Create bad fixture: `tests/fixtures/redundant_super_init/bad/multiple_inheritance_violation.py` with multiple parents, one violates
- [ ] T048 [P] [US3] Write test in `tests/test_check_redundant_super_init.py`: test_detects_redundant_kwargs_forwarding (violation case)
- [ ] T049 [P] [US3] Write test in `tests/test_check_redundant_super_init.py`: test_no_violation_when_parent_accepts_kwargs (good case)
- [ ] T050 [P] [US3] Write test in `tests/test_check_redundant_super_init.py`: test_no_violation_when_no_kwargs (child has no **kwargs)
- [ ] T051 [P] [US3] Write test in `tests/test_check_redundant_super_init.py`: test_skips_unresolvable_parents (parent from import)
- [ ] T052 [P] [US3] Write test in `tests/test_check_redundant_super_init.py`: test_handles_multiple_inheritance (complex case)
- [ ] T053 [P] [US3] Write test in `tests/test_check_redundant_super_init.py`: test_handles_syntax_errors_gracefully (edge case)

### Implementation for User Story 3

- [ ] T054 [US3] Implement CLI argument parsing in `src/pre_commit_hooks/check_redundant_super_init.py`: argparse with filenames (no --fix flag)
- [ ] T055 [US3] Implement AST parsing in `src/pre_commit_hooks/check_redundant_super_init.py`: use ast.parse() to build AST from source
- [ ] T056 [US3] Implement SuperInitChecker visitor class in `src/pre_commit_hooks/check_redundant_super_init.py`: extend ast.NodeVisitor
- [ ] T057 [US3] Implement visit_ClassDef in `src/pre_commit_hooks/check_redundant_super_init.py`: collect class definitions and analyze __init__
- [ ] T058 [US3] Implement __init__ signature analysis in `src/pre_commit_hooks/check_redundant_super_init.py`: check for **kwargs parameter
- [ ] T059 [US3] Implement super().__init__() call detection in `src/pre_commit_hooks/check_redundant_super_init.py`: find Call nodes with super().__init__
- [ ] T060 [US3] Implement **kwargs forwarding detection in `src/pre_commit_hooks/check_redundant_super_init.py`: check if **kwargs passed to super()
- [ ] T061 [US3] Implement parent signature resolution in `src/pre_commit_hooks/check_redundant_super_init.py`: resolve parent __init__ from same file
- [ ] T062 [US3] Implement violation detection logic in `src/pre_commit_hooks/check_redundant_super_init.py`: compare child/parent signatures
- [ ] T063 [US3] Implement main() entry point in `src/pre_commit_hooks/check_redundant_super_init.py`: process multiple files, report violations
- [ ] T064 [US3] Add error handling for syntax errors in `src/pre_commit_hooks/check_redundant_super_init.py`: catch ast.SyntaxError
- [ ] T065 [US3] Add module docstring and inline comments in `src/pre_commit_hooks/check_redundant_super_init.py`: explain AST visitor pattern

**Checkpoint**: All user stories should now be independently functional. Run `pytest tests/test_check_redundant_super_init.py` to verify US3.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration, documentation, and finalization across all three hooks

- [ ] T066 [P] Update `.pre-commit-hooks.yaml` with three new hook entries: fix-misplaced-comments, fix-excessive-blank-lines, check-redundant-super-init
- [ ] T067 [P] Update `README.md` with hook descriptions: add STYLE-001, STYLE-002, MAINTAINABILITY-006 sections with examples
- [ ] T068 [P] Add usage examples to `README.md`: show .pre-commit-config.yaml configuration for all three hooks
- [ ] T069 Run all tests with coverage: `pytest --cov=src/pre_commit_hooks --cov-report=term-missing` (target >90% coverage)
- [ ] T070 [P] Run ruff linting on all hook implementations: `ruff check src/pre_commit_hooks/`
- [ ] T071 [P] Run ruff linting on all tests: `ruff check tests/`
- [ ] T072 Test hooks on real Python files: run all three hooks on `src/` directory to validate on actual code
- [ ] T073 Verify quickstart.md examples: ensure all code snippets in quickstart.md are accurate
- [ ] T074 Create release notes documenting the three new hooks and their purpose
- [ ] T075 Tag release with appropriate version bump (e.g., v1.1.0 for new features)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: No foundational phase - hooks are independent
- **User Stories (Phase 3-5)**: All can start immediately after Setup (Phase 1)
  - US1, US2, US3 are completely independent - can proceed in parallel
  - Or sequentially in priority order (P1 → P2 → P3) for MVP approach
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Setup - No dependencies on other stories
- **User Story 3 (P3)**: Can start after Setup - No dependencies on other stories

**Key Insight**: All three hooks are completely independent. They:
- Use different Python stdlib modules (tokenize vs line processing vs AST)
- Operate on different files (no file conflicts)
- Have no shared code or dependencies
- Can be developed, tested, and deployed independently

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Test fixtures before test code
- All tests for a story can run in parallel (marked with [P])
- Implementation tasks run sequentially (each builds on previous)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks T002-T004 can run in parallel
- All three user stories can run in parallel (if team capacity allows)
- Within each user story:
  - All test fixture creation tasks can run in parallel
  - All test writing tasks can run in parallel
- Polish tasks T066-T068, T070-T071 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Phase: Tests - Launch all test fixture creation together:
Task T005: "Create good fixture: tests/fixtures/misplaced_comments/good/inline_comment.py"
Task T006: "Create good fixture: tests/fixtures/misplaced_comments/good/preceding_comment.py"
Task T007: "Create bad fixture: tests/fixtures/misplaced_comments/bad/trailing_on_paren.py"
Task T008: "Create bad fixture: tests/fixtures/misplaced_comments/bad/trailing_on_bracket.py"
Task T009: "Create bad fixture: tests/fixtures/misplaced_comments/bad/trailing_on_brace.py"

# Phase: Tests - Launch all test writing together:
Task T010: "Write test: test_detects_trailing_comment_on_closing_paren"
Task T011: "Write test: test_fixes_trailing_comment_inline_placement"
Task T012: "Write test: test_fixes_trailing_comment_preceding_placement"
Task T013: "Write test: test_no_violation_for_correct_code"
Task T014: "Write test: test_handles_syntax_errors_gracefully"
Task T015: "Write test: test_preserves_file_encoding_and_line_endings"

# Phase: Implementation - Run sequentially (each builds on previous):
Task T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024
```

---

## Parallel Example: All Three User Stories

```bash
# After Setup (Phase 1) completes, launch all three stories in parallel:

# Developer A works on User Story 1:
Tasks T005-T024 (fix-misplaced-comments hook)

# Developer B works on User Story 2:
Tasks T025-T043 (fix-excessive-blank-lines hook)

# Developer C works on User Story 3:
Tasks T044-T065 (check-redundant-super-init hook)

# Stories complete independently and can be merged/deployed separately
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 3: User Story 1 (T005-T024)
3. **STOP and VALIDATE**: Test US1 independently with `pytest tests/test_fix_misplaced_comments.py`
4. Test manually: `python -m pre_commit_hooks.fix_misplaced_comments --fix src/**/*.py`
5. Deploy/demo fix-misplaced-comments hook (MVP!)

### Incremental Delivery

1. Complete Setup (Phase 1) → Foundation ready
2. Add User Story 1 (Phase 3) → Test independently → Deploy/Demo (MVP - fix-misplaced-comments)
3. Add User Story 2 (Phase 4) → Test independently → Deploy/Demo (fix-excessive-blank-lines)
4. Add User Story 3 (Phase 5) → Test independently → Deploy/Demo (check-redundant-super-init)
5. Add Polish (Phase 6) → Final release with all three hooks

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together (Phase 1)
2. Once Setup is done:
   - Developer A: User Story 1 (T005-T024)
   - Developer B: User Story 2 (T025-T043)
   - Developer C: User Story 3 (T044-T065)
3. Stories complete independently
4. Team collaborates on Polish (Phase 6)

---

## Task Summary

**Total Tasks**: 75

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 0 tasks (no blocking prerequisites)
- Phase 3 (US1): 20 tasks (11 tests + 9 implementation)
- Phase 4 (US2): 19 tasks (10 tests + 9 implementation)
- Phase 5 (US3): 22 tasks (10 tests + 12 implementation)
- Phase 6 (Polish): 10 tasks

**By Type**:
- Setup/Infrastructure: 4 tasks
- Test Fixtures: 15 tasks (5 per hook)
- Test Code: 16 tasks (5-6 per hook)
- Implementation: 30 tasks (9-12 per hook)
- Documentation/Polish: 10 tasks

**Parallel Opportunities**:
- Setup phase: 3 tasks can run in parallel
- All 3 user stories can run in parallel (completely independent)
- Within each story: 5-6 test fixture tasks can run in parallel
- Within each story: 5-6 test writing tasks can run in parallel
- Polish phase: 5 tasks can run in parallel

**MVP Scope**: Phase 1 + Phase 3 = 24 tasks (fix-misplaced-comments hook only)

**Independent Test Criteria**:
- **US1**: Run `pytest tests/test_fix_misplaced_comments.py && python -m pre_commit_hooks.fix_misplaced_comments --fix tests/fixtures/misplaced_comments/bad/*.py`
- **US2**: Run `pytest tests/test_fix_excessive_blank_lines.py && python -m pre_commit_hooks.fix_excessive_blank_lines --fix tests/fixtures/excessive_blank_lines/bad/*.py`
- **US3**: Run `pytest tests/test_check_redundant_super_init.py && python -m pre_commit_hooks.check_redundant_super_init tests/fixtures/redundant_super_init/bad/*.py`

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label (US1, US2, US3) maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (TDD approach)
- All hooks use Python stdlib only (no external dependencies)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Hooks are completely independent - maximum parallelization possible
