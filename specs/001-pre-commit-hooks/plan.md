# Implementation Plan: Custom Pre-Commit Hooks Repository

**Branch**: `001-pre-commit-hooks` | **Date**: 2025-11-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-pre-commit-hooks/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a custom pre-commit hooks repository with an initial hook ("forbid-vars") that prevents commits containing forbidden variable names like `data` and `result`. The hook will support configurable blacklists via hook args, inline ignore comments, and provide helpful error messages linking to best practices. Following the KISS principle from the constitution, this will be implemented as a Python script (since pattern matching across multiple file types requires more than basic bash/git commands). The repository will follow the pre-commit framework's `.pre-commit-hooks.yaml` schema and be distributed as a public GitHub repository.

## Technical Context

**Language/Version**: Python 3.8+ (minimum version compatible with most development environments; pre-commit supports Python 3.8+)
**Primary Dependencies**: None (Python standard library only per FR-012 and Constitution I - KISS principle)
**Storage**: N/A (hooks process files passed as arguments; no persistent storage needed)
**Testing**: pytest (de facto standard for Python testing; will validate exit codes, error messages, and edge cases)
**Target Platform**: Cross-platform (Linux, macOS, Windows) - pre-commit runs wherever Python and git are available
**Project Type**: Single project (Python-based pre-commit hook scripts with configuration metadata)
**Performance Goals**: <5 seconds for repositories with <1000 files (per SC-002); O(n) complexity where n = number of files checked
**Constraints**:

- Must use only Python stdlib (no external dependencies - constitution I, FR-012)
- Must return exit code 0 for success, non-zero for failure (FR-003, Constitution III)
- Must accept file paths as CLI arguments (pre-commit framework requirement - FR-009, Constitution III)
- Must provide actionable error messages (FR-004, Constitution III)
  **Scale/Scope**: MVP: 1 hook (forbid-vars), scales to 5+ hooks in subsequent phases (SC-005)

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### Constitution I: KISS Principle - Implementation Strategy ✅ PASS

**Rule**: Prefer Bash + Git commands; fall back to Python only when necessary.

**Assessment**:

- The forbid-vars hook requires pattern matching across source code files for variable name detection
- Implementing this in bash would require complex regex patterns and text processing that is error-prone and hard to maintain
- Python provides clearer, more maintainable pattern matching with the `re` module (stdlib)
- **Decision**: Python is justified for this hook; bash/git alone would be overly complex

**Status**: ✅ PASS (Python fallback is appropriate for pattern matching complexity)

### Constitution II: Code Quality - Mandatory Linting ✅ PASS

**Rule**: All code must pass appropriate linters (shellcheck for bash, ruff for Python, prettier for markdown/yaml).

**Assessment**:

- Will use ruff for Python hook scripts (PEP 8 compliance)
- Will use prettier for .pre-commit-hooks.yaml and README.md
- Will enforce linting via pre-commit hooks on this repository itself
- All linting enforced before merge

**Status**: ✅ PASS (linting strategy defined and will be implemented)

### Constitution III: Pre-commit Framework Compatibility ✅ PASS

**Rule**: Hooks must follow pre-commit conventions (.pre-commit-hooks.yaml schema, file path args, exit codes, stderr messages, idempotent).

**Assessment**:

- Will create `.pre-commit-hooks.yaml` following official schema
- Hooks will accept file paths as CLI arguments (FR-009)
- Exit code 0 for success, non-zero for failure (FR-003)
- Error messages to stderr with actionable guidance (FR-004)
- Hooks are read-only (idempotent checks, no file modification)

**Status**: ✅ PASS (all pre-commit compatibility requirements addressed in technical context)

### Constitution IV: Testing Requirements ✅ PASS

**Rule**: Every hook must include automated tests for success cases, failure cases, edge cases, and independence.

**Assessment**:

- Will use pytest for automated testing (specified in Technical Context)
- Test plan includes:
  - Success: files without forbidden vars → exit 0
  - Failure: files with forbidden vars → exit 1 + error message
  - Edge cases: empty files, binary files, inline ignore comments, custom blacklists
  - Independence: tests will invoke hook script directly (no git/pre-commit dependency)
- 100% coverage target for hook logic

**Status**: ✅ PASS (comprehensive testing strategy defined)

### Constitution V: Simplicity and Maintainability ✅ PASS

**Rule**: Hooks must be simple, single-purpose, readable, well-commented, independently understandable.

**Assessment**:

- forbid-vars has single purpose: detect forbidden variable names
- Logic will be straightforward: read files, regex match, report violations
- Will include comments explaining regex patterns and ignore logic
- Error messages explain "why" (link to meaningless variable names article)
- Minimal coupling (standalone hook, no dependencies on other hooks)

**Status**: ✅ PASS (simplicity and clarity prioritized in design)

### Summary

**Overall Status**: ✅ ALL GATES PASSED

All constitutional principles are satisfied. No violations require justification. Proceeding to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
pre_commit_extra_hooks/           # Repository root
├── .pre-commit-hooks.yaml        # Hook metadata (defines available hooks for pre-commit framework)
├── README.md                     # User documentation (FR-005, FR-007)
├── LICENSE                       # Open source license
├── .pre-commit-config.yaml       # Self-dogfooding: use our own hooks + ruff/prettier
├── pyproject.toml                # Python project metadata (minimal, no dependencies)
│
├── pre_commit_hooks/             # Hook scripts directory
│   ├── __init__.py
│   └── forbid_vars.py            # Initial hook: forbid variable names
│
└── tests/                        # Test suite (Constitution IV, FR-006)
    ├── __init__.py
    ├── test_forbid_vars.py       # Tests for forbid-vars hook
    └── fixtures/                 # Test data (sample files for validation)
        ├── valid_code.py         # Files without forbidden vars
        ├── invalid_code.py       # Files with forbidden vars
        └── ignored_code.py       # Files with inline ignore comments
```

**Structure Decision**: Single project structure. This is a Python-based pre-commit hooks repository following the standard pattern established by [pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks). Hook scripts live in `pre_commit_hooks/` directory, tests in `tests/`, and `.pre-commit-hooks.yaml` at the root defines hook metadata for the pre-commit framework.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All constitutional gates passed (see Constitution Check section above).

---

## Post-Design Constitution Re-evaluation

_Phase 1 complete. Re-checking constitutional compliance after design artifacts._

### Constitution I: KISS Principle ✅ PASS (CONFIRMED)

**Post-design assessment:**

- Research confirmed AST-based approach is simpler and more accurate than regex
- No external dependencies in final design (stdlib only)
- Data model is minimal (3 entities, all ephemeral)
- Implementation uses standard Python patterns (ast.NodeVisitor)

**Status**: ✅ PASS - Design maintains KISS principle

### Constitution II: Code Quality - Mandatory Linting ✅ PASS (CONFIRMED)

**Post-design assessment:**

- Contracts define linting strategy (ruff for Python, prettier for YAML/markdown)
- pyproject.toml.example includes ruff configuration
- Self-dogfooding planned (.pre-commit-config.yaml to run own hooks + linters)

**Status**: ✅ PASS - Linting fully integrated into design

### Constitution III: Pre-commit Framework Compatibility ✅ PASS (CONFIRMED)

**Post-design assessment:**

- hook-schema.yaml defines complete pre-commit contract
- CLI interface follows standard pattern (argparse, file paths, exit codes)
- .pre-commit-hooks.yaml.example shows proper hook metadata
- Error message format follows linter conventions (file:line: message)

**Status**: ✅ PASS - Full pre-commit compatibility designed

### Constitution IV: Testing Requirements ✅ PASS (CONFIRMED)

**Post-design assessment:**

- hook-schema.yaml defines comprehensive test categories:
  - Success cases (empty files, valid names)
  - Failure cases (forbidden names in assignments, parameters)
  - Ignore comment handling (inline suppression)
  - Edge cases (syntax errors, binary files, performance)
  - CLI argument handling (custom blacklists)
- Test independence: hook can be invoked directly (no git/pre-commit needed)
- pytest configuration in pyproject.toml.example

**Status**: ✅ PASS - Testing strategy comprehensive and independent

### Constitution V: Simplicity and Maintainability ✅ PASS (CONFIRMED)

**Post-design assessment:**

- Data model is minimal (3 entities, no persistence)
- Single-purpose design (only detects forbidden variable names)
- Clear separation of concerns:
  - AST visitor (detection)
  - Tokenizer (ignore comment parsing)
  - CLI (file processing, reporting)
- Well-documented in research.md with rationale for all decisions
- Contracts provide clear API boundaries

**Status**: ✅ PASS - Design is simple, clear, and maintainable

### Post-Design Summary

**Overall Status**: ✅ ALL GATES PASSED (RE-CONFIRMED)

After completing Phase 0 (research) and Phase 1 (design), all constitutional principles remain satisfied:

- AST-based implementation justified and documented
- Linting strategy fully defined
- Pre-commit compatibility ensured via contracts
- Comprehensive testing planned
- Simple, maintainable design with clear documentation

**Phase 1 Complete**. Ready for Phase 2 (tasks generation via `/speckit.tasks`).

---

## Phase 0 & 1 Artifacts Generated

### Phase 0: Research

- ✅ `research.md` - Comprehensive research on AST patterns, ignore comments, error messages, pre-commit schema

### Phase 1: Design

- ✅ `data-model.md` - Entity definitions, state transitions, data structures
- ✅ `contracts/hook-schema.yaml` - Complete API contract (CLI, exit codes, output format, compatibility)
- ✅ `contracts/pre-commit-hooks.yaml.example` - Example hook metadata file
- ✅ `contracts/pyproject.toml.example` - Example Python project configuration
- ✅ `quickstart.md` - User guide for installing and using the hook
- ✅ `CLAUDE.md` - Updated agent context with project technology stack

---

## Next Steps

The implementation plan is complete. To proceed with implementation:

1. **Generate tasks**: Run `/speckit.tasks` to create actionable implementation tasks
2. **Implement hook**: Follow tasks to build `pre_commit_hooks/forbid_vars.py`
3. **Write tests**: Create comprehensive test suite in `tests/test_forbid_vars.py`
4. **Add documentation**: Create README.md with usage examples
5. **Configure linting**: Set up .pre-commit-config.yaml to dogfood own hooks
6. **Test end-to-end**: Verify hook works in real pre-commit workflow
