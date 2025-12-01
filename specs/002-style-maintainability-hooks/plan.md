# Implementation Plan: Style and Maintainability Pre-commit Hooks

**Branch**: `002-style-maintainability-hooks` | **Date**: 2025-11-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-style-maintainability-hooks/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement three Python-based pre-commit hooks that detect and fix code quality issues: STYLE-001 (misplaced comments on closing brackets), STYLE-002 (excessive blank lines after module headers), and MAINTAINABILITY-006 (redundant super().**init**(\*\*kwargs) forwarding). These hooks extend the existing pre-commit hooks repository to enforce style and maintainability standards using Python's AST and tokenize modules from the standard library.

## Technical Context

**Language/Version**: Python 3.8+ (minimum version - pre-commit framework supports 3.8+)
**Primary Dependencies**: Python standard library only (ast, tokenize, inspect, argparse, sys, pathlib)
**Storage**: N/A (hooks process files in-place, no persistent storage needed)
**Testing**: pytest with coverage reporting
**Target Platform**: Linux (primary), macOS, Windows (pre-commit runs on all platforms)
**Project Type**: Single project (CLI tools - pre-commit hooks are executable scripts)
**Performance Goals**: Process up to 10,000 lines of code in under 5 seconds; individual file processing <1 second per 1000 lines
**Constraints**: No external dependencies beyond Python stdlib; must preserve file encoding and line endings; must handle syntax errors gracefully; max line length 88 chars (Black default) for inline comment placement
**Scale/Scope**: 3 independent hooks; each hook analyzes/modifies Python source files; hooks integrate with existing .pre-commit-hooks.yaml configuration

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### I. KISS Principle - Implementation Strategy

**Status**: ⚠️ **EXCEPTION REQUIRED** - Using Python instead of Bash

**Justification**:

- These hooks require AST parsing and token-level analysis of Python source code
- Bash cannot parse Python AST or reliably manipulate source code while preserving semantics
- The tasks (comment placement, blank line detection, class hierarchy analysis) are inherently Python-specific and require Python's ast/tokenize modules
- Attempting this in Bash would require spawning Python anyway or result in fragile regex-based parsing

**Simpler Alternative Rejected**: Bash + grep/sed/awk would be error-prone, unable to handle Python's complex syntax (nested brackets, multi-line statements, string literals containing comment-like characters), and ultimately less maintainable than purpose-built Python code.

### II. Code Quality - Mandatory Linting

**Status**: ✅ **PASS**

- All Python code will be linted with ruff (already in repository pre-commit config)
- All Markdown documentation will be formatted with prettier
- CI enforces linting before merge

### III. Pre-commit Framework Compatibility

**Status**: ✅ **PASS**

- All hooks will accept file paths as command-line arguments
- Exit code 0 for success, non-zero for violations
- Actionable error messages written to stderr with file:line:message format
- Hooks are idempotent (running twice produces same result)
- Auto-fix mode explicitly documented in .pre-commit-hooks.yaml with `types: [python]`

### IV. Testing Requirements

**Status**: ✅ **PASS**

- Each hook will have comprehensive pytest tests in tests/
- Tests will validate success cases, failure cases, edge cases (syntax errors, empty files, complex syntax)
- Tests will validate error message quality (not just exit codes)
- Tests run independently without requiring git or pre-commit installed

### V. Simplicity and Maintainability

**Status**: ✅ **PASS**

- Each hook has single, well-defined purpose (one rule per hook)
- Code will be commented to explain AST traversal logic and regex patterns
- Hooks are independent (no shared state or coupling between hooks)
- Documentation will explain "why" each rule matters for code quality

**Overall**: ✅ **APPROVED** with justified exception to KISS principle for Python usage

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
src/
├── pre_commit_hooks/
│   ├── __init__.py
│   ├── fix_misplaced_comments.py      # STYLE-001 hook implementation
│   ├── fix_excessive_blank_lines.py   # STYLE-002 hook implementation
│   └── check_redundant_super_init.py  # MAINTAINABILITY-006 hook implementation

tests/
├── test_fix_misplaced_comments.py
├── test_fix_excessive_blank_lines.py
├── test_check_redundant_super_init.py
└── fixtures/                          # Test input files (good/bad examples)
    ├── misplaced_comments/
    ├── excessive_blank_lines/
    └── redundant_super_init/

.pre-commit-hooks.yaml                 # Hook registry (updated with 3 new hooks)
README.md                              # Documentation (updated with hook descriptions)
```

**Structure Decision**: Single project structure using existing src/ and tests/ directories. Each hook is implemented as a standalone Python script that can be invoked directly by pre-commit framework. Test fixtures organized by hook type to provide clean separation of test data.

## Complexity Tracking

| Violation              | Why Needed                                                               | Simpler Alternative Rejected Because                                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python instead of Bash | Hooks require AST parsing and token-level analysis of Python source code | Bash cannot parse Python AST; regex-based approaches would be fragile and unable to handle nested syntax, multi-line statements, or comments in strings |
