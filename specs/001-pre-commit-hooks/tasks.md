# Tasks: Custom Pre-Commit Hooks Repository

**Input**: Design documents from `/specs/001-pre-commit-hooks/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included per Constitution IV requirement (comprehensive testing for all hooks)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project structure:
- `pre_commit_hooks/` - Hook implementation scripts
- `tests/` - Test suite
- Repository root - Configuration files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (pre_commit_hooks/, tests/, tests/fixtures/)
- [X] T002 Create pyproject.toml with Python 3.8+ configuration and entry points
- [X] T003 [P] Create LICENSE file (MIT license)
- [X] T004 [P] Create .gitignore for Python projects
- [X] T005 [P] Create pre_commit_hooks/__init__.py module file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Configure ruff linting in pyproject.toml per Constitution II
- [X] T007 [P] Configure pytest in pyproject.toml for test execution
- [X] T008 [P] Create .pre-commit-config.yaml for self-dogfooding (ruff + prettier)
- [X] T009 Create tests/__init__.py module file

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Using Custom Hooks in a Project (Priority: P1) 🎯 MVP

**Goal**: Deliver working forbid-vars hook that developers can use in their projects via pre-commit framework

**Independent Test**: Add repository to a test project's .pre-commit-config.yaml, commit code with forbidden variable names, verify hook blocks commit with clear error messages

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Create tests/fixtures/valid_code.py with code using descriptive variable names
- [X] T011 [P] [US1] Create tests/fixtures/invalid_code.py with code using 'data' and 'result' variables
- [X] T012 [P] [US1] Create tests/fixtures/ignored_code.py with forbidden names + ignore comments
- [X] T013 [US1] Write test_forbid_vars.py: test_success_case (exit 0 for valid code) in tests/test_forbid_vars.py
- [X] T014 [US1] Write test_forbid_vars.py: test_failure_case (exit 1, error messages for invalid code) in tests/test_forbid_vars.py
- [X] T015 [US1] Write test_forbid_vars.py: test_ignore_comment (exit 0 when inline ignore used) in tests/test_forbid_vars.py
- [X] T016 [US1] Write test_forbid_vars.py: test_custom_blacklist (--names argument works) in tests/test_forbid_vars.py
- [X] T017 [US1] Write test_forbid_vars.py: test_empty_file (exit 0 for empty file) in tests/test_forbid_vars.py
- [X] T018 [US1] Write test_forbid_vars.py: test_syntax_error (graceful handling of invalid Python) in tests/test_forbid_vars.py
- [X] T019 [US1] Write test_forbid_vars.py: test_function_parameters (detects forbidden names in function params) in tests/test_forbid_vars.py
- [X] T020 [US1] Write test_forbid_vars.py: test_multiple_violations (reports all violations in file) in tests/test_forbid_vars.py

### Implementation for User Story 1

- [X] T021 [US1] Implement ForbiddenNameVisitor class (ast.NodeVisitor) in pre_commit_hooks/forbid_vars.py
- [X] T022 [US1] Implement visit_Assign method (detect regular assignments) in pre_commit_hooks/forbid_vars.py
- [X] T023 [US1] Implement visit_AnnAssign method (detect annotated assignments) in pre_commit_hooks/forbid_vars.py
- [X] T024 [US1] Implement visit_FunctionDef method (detect function parameters) in pre_commit_hooks/forbid_vars.py
- [X] T025 [US1] Implement visit_AsyncFunctionDef method (detect async function parameters) in pre_commit_hooks/forbid_vars.py
- [X] T026 [US1] Implement get_ignored_lines function (tokenize-based comment parsing) in pre_commit_hooks/forbid_vars.py
- [X] T027 [US1] Implement check_file function (AST parsing, violation filtering) in pre_commit_hooks/forbid_vars.py
- [X] T028 [US1] Implement main CLI function (argparse, file processing, exit codes) in pre_commit_hooks/forbid_vars.py
- [X] T029 [US1] Add error message formatting per contract (file:line: message + link) in pre_commit_hooks/forbid_vars.py
- [X] T030 [US1] Configure forbid-vars entry point in pyproject.toml [project.scripts]
- [X] T031 [US1] Create .pre-commit-hooks.yaml with forbid-vars hook metadata at repository root
- [X] T032 [US1] Run all tests and verify they pass with pytest
- [X] T032b [US1] Validate FR-006: run forbid-vars hook script directly (not via pre-commit) with file paths to prove independence
- [X] T033 [US1] Run ruff linter and fix any issues in pre_commit_hooks/forbid_vars.py

**Checkpoint**: At this point, User Story 1 should be fully functional - the forbid-vars hook works end-to-end

---

## Phase 4: User Story 2 - Adding New Custom Hooks (Priority: P2)

**Goal**: Establish clear patterns and documentation so developers can easily add new hooks to the repository

**Independent Test**: Follow documentation to create a new hook script, add configuration, verify it runs in pre-commit

### Implementation for User Story 2

- [X] T034 [P] [US2] Create README.md with repository overview and hook listing at repository root
- [X] T035 [US2] Document forbid-vars hook: purpose, usage, configuration in README.md
- [X] T036 [US2] Add "Adding New Hooks" section to README.md with step-by-step guide
- [X] T037 [US2] Add .pre-commit-config.yaml usage examples to README.md per FR-007
- [X] T038 [US2] Document project structure and conventions in README.md
- [X] T039 [US2] Add "Testing Hooks" section explaining how to test independently per FR-006
- [X] T040 [US2] Add "Configuration Options" section for hook arguments in README.md
- [X] T041 [P] [US2] Create inline .pre-commit-config.yaml example snippet in README.md showing forbid-vars usage
- [X] T041b [P] [US2] Create .pre-commit-config.yaml.example file at repository root with complete configuration examples per FR-007

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - hook works and documentation enables adding more hooks

---

## Phase 5: User Story 3 - Maintaining and Updating Hooks (Priority: P3)

**Goal**: Establish versioning, testing, and compatibility practices for long-term hook maintenance

**Independent Test**: Tag a release, run pre-commit autoupdate in test project, verify hook still functions

### Implementation for User Story 3

- [ ] T042 [P] [US3] Add CONTRIBUTING.md with guidelines for hook updates at repository root
- [ ] T043 [US3] Document semantic versioning strategy in CONTRIBUTING.md per FR-011
- [ ] T043b [US3] Add to README.md: how users should reference tags in .pre-commit-config.yaml (rev: v1.0.0 syntax) to enable autoupdate
- [ ] T044 [US3] Add backward compatibility guidelines to CONTRIBUTING.md
- [ ] T045 [US3] Add performance testing section to CONTRIBUTING.md (SC-002 requirement)
- [ ] T046 [US3] Document release process (tagging, changelog) in CONTRIBUTING.md
- [ ] T047 [US3] Add troubleshooting section to README.md (common issues, solutions)
- [ ] T048 [US3] Create initial git tag v1.0.0 for first release
- [ ] T049 [US3] Add CI/CD configuration recommendations to CONTRIBUTING.md

**Checkpoint**: All user stories should now be independently functional with full lifecycle support

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Add inline code comments explaining AST visitor logic in pre_commit_hooks/forbid_vars.py
- [ ] T051 [P] Add docstrings to all functions and classes in pre_commit_hooks/forbid_vars.py
- [ ] T052 [P] Verify error messages meet SC-003 (include what/where/how per spec)
- [ ] T052b [P] Manual validation: test error messages with fresh eyes (simulate new user, verify fix-ability without docs)
- [ ] T053 Run prettier on .pre-commit-hooks.yaml and README.md
- [ ] T054 Verify hook processes <1000 files in <5 seconds (SC-002 performance check)
- [ ] T055 Test hook on Linux, macOS, Windows environments per SC-006
- [ ] T056 [P] Add badge links to README.md (pre-commit compatible, Python version)
- [ ] T057 Validate quickstart.md scenarios manually (install, use, configure)
- [ ] T058 Run full test suite with pytest and ensure 100% pass rate
- [ ] T059 Final constitutional compliance check (all 5 principles met)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T005) - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion (T006-T009)
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after US1 is complete (needs hook to document) - Depends on T021-T033
- **User Story 3 (P3)**: Can start after US1 is complete (needs hook to maintain) - Depends on T021-T033

### Within Each User Story

- **User Story 1**:
  - Tests (T010-T020) MUST be written and FAIL before implementation
  - Test fixtures (T010-T012) can be created in parallel
  - Tests (T013-T020) can be written in parallel after fixtures exist
  - Implementation (T021-T033) follows tests
  - AST visitor methods (T021-T025) can be partially parallelized (different files/sections)
  - T032 (run tests) depends on all implementation tasks
  - T033 (linting) can run in parallel with T032

- **User Story 2**:
  - All documentation tasks can be parallelized (T034-T041 marked [P] where applicable)

- **User Story 3**:
  - Most documentation tasks can be parallelized (T042-T049 marked [P] where applicable)

### Parallel Opportunities

Within Setup (Phase 1):
- T003, T004, T005 can run in parallel

Within Foundational (Phase 2):
- T007, T008, T009 can run in parallel after T006

Within User Story 1:
- Test fixtures (T010, T011, T012) can run in parallel
- Test writing (T013-T020) can run in parallel after fixtures
- AST visitor implementation (T022-T025) can overlap (different methods)

Within User Story 2:
- Most README sections (T034, T035, T036, T037, T038, T039, T040) can be written in parallel

Within User Story 3:
- CONTRIBUTING.md sections (T042, T043, T044, T045, T046) can be written in parallel

Within Polish (Phase 6):
- T050, T051, T052, T056 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all test fixtures for User Story 1 together:
Task T010: "Create tests/fixtures/valid_code.py with code using descriptive variable names"
Task T011: "Create tests/fixtures/invalid_code.py with code using 'data' and 'result' variables"
Task T012: "Create tests/fixtures/ignored_code.py with forbidden names + ignore comments"

# Launch all test cases for User Story 1 together (after fixtures exist):
Task T013: "Write test_forbid_vars.py: test_success_case (exit 0 for valid code)"
Task T014: "Write test_forbid_vars.py: test_failure_case (exit 1, error messages for invalid code)"
Task T015: "Write test_forbid_vars.py: test_ignore_comment (exit 0 when inline ignore used)"
# ... (T016-T020 also in parallel)

# Implementation tasks run sequentially or with limited parallelization
# (different methods in same file - can be done by same developer incrementally)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T009) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T010-T033)
4. **STOP and VALIDATE**: Test forbid-vars hook independently:
   - Create test project with .pre-commit-config.yaml
   - Add this repo as a hook source
   - Try committing forbidden variable names
   - Verify hook blocks commit with clear error message
   - Try committing good code → verify hook passes
5. Tag v1.0.0 and consider MVP complete!

### Incremental Delivery

1. Complete Setup + Foundational (T001-T009) → Foundation ready
2. Add User Story 1 (T010-T033) → Test independently → Tag v1.0.0 (MVP!)
3. Add User Story 2 (T034-T041) → Verify documentation clarity → Tag v1.1.0
4. Add User Story 3 (T042-T049) → Verify maintainability → Tag v1.2.0
5. Polish (T050-T059) → Final quality pass → Tag v2.0.0
6. Each increment adds value without breaking previous functionality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T009)
2. Once Foundational is done:
   - Developer A: Focus on User Story 1 (T010-T033) - highest priority
   - Developer B: Prepare User Story 2 docs in draft (can't complete until US1 done)
   - Developer C: Research additional hooks for future phases
3. After US1 complete:
   - Developer A: Move to Polish tasks
   - Developer B: Finalize US2 documentation
   - Developer C: Finalize US3 maintenance docs

---

## Task Count Summary

- **Total Tasks**: 63
- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 4 tasks
- **Phase 3 (US1 - forbid-vars hook)**: 25 tasks (11 tests + 14 implementation)
- **Phase 4 (US2 - extensibility)**: 9 tasks
- **Phase 5 (US3 - maintenance)**: 9 tasks
- **Phase 6 (Polish)**: 11 tasks

**Parallelizable**: 26 tasks marked [P]

**MVP Scope**: Phases 1-3 (34 tasks) deliver a working hook

---

## Notes

- [P] tasks = different files or independent sections, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach per Constitution IV)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution compliance verified throughout (KISS, linting, pre-commit compat, testing, simplicity)
- All file paths are absolute from repository root
- Python 3.8+ compatibility maintained throughout
- No external dependencies (stdlib only per FR-012)
