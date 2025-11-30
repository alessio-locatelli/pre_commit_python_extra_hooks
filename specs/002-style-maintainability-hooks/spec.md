# Feature Specification: Style and Maintainability Pre-commit Hooks

**Feature Branch**: `002-style-maintainability-hooks`
**Created**: 2025-11-30
**Status**: Draft
**Input**: User description: "Three pre-commit hooks for Python code quality: STYLE-001 (misplaced comments), STYLE-002 (excessive blank lines), and MAINTAINABILITY-006 (redundant super init kwargs)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect and Fix Misplaced Comments (Priority: P1)

As a Python developer, I want trailing comments on closing brackets to be automatically moved to the correct line so that my code remains readable after auto-formatting tools run.

**Why this priority**: This is the most common style issue that degrades code readability. When formatters like Black or Ruff move closing parentheses to new lines, comments that were inline with arguments end up orphaned on closing bracket lines, losing their contextual meaning.

**Independent Test**: Can be fully tested by running the hook on a file with trailing comments on closing brackets and verifying the comments are moved to the appropriate line (either inline with the expression or as a preceding comment).

**Acceptance Scenarios**:

1. **Given** a Python file with a trailing comment on a closing parenthesis line, **When** the hook runs, **Then** the comment is moved to the line containing the expression it describes
2. **Given** a Python file with a short expression and inline comment potential, **When** the hook runs, **Then** the comment is placed inline with the expression
3. **Given** a Python file with a long expression, **When** the hook runs, **Then** the comment is placed as a preceding `#` comment on the line above the expression
4. **Given** a Python file with comments already in correct positions, **When** the hook runs, **Then** no changes are made and the hook passes

---

### User Story 2 - Detect and Fix Excessive Blank Lines (Priority: P2)

As a Python developer, I want multiple consecutive blank lines after module headers or top comments to be collapsed to a single blank line so that my code follows consistent spacing conventions.

**Why this priority**: While less critical than comment placement, excessive blank lines create unnecessary whitespace that reduces code density and can distract from the logical structure. This is important for maintaining clean, professional codebases.

**Independent Test**: Can be fully tested by running the hook on files with multiple blank lines after module docstrings/comments and verifying they are collapsed to a single blank line while preserving copyright notice spacing.

**Acceptance Scenarios**:

1. **Given** a Python file with 2+ blank lines after a module-level comment, **When** the hook runs, **Then** the blank lines are collapsed to exactly one blank line
2. **Given** a Python file with 2+ blank lines after a module docstring, **When** the hook runs, **Then** the blank lines are collapsed to exactly one blank line
3. **Given** a Python file with a copyright comment followed by one blank line, **When** the hook runs, **Then** the spacing is preserved (copyright requires one blank line separator)
4. **Given** a Python file with already-correct spacing, **When** the hook runs, **Then** no changes are made and the hook passes

---

### User Story 3 - Detect Redundant Super Init Kwargs (Priority: P3)

As a Python developer, I want to detect when I'm forwarding `**kwargs` to a parent `__init__` that doesn't accept any arguments so that I can avoid creating misleading inheritance chains.

**Why this priority**: While important for code maintainability, this issue is less frequent than style issues and typically doesn't impact runtime behavior. It's more about preventing confusing patterns that make code harder to understand.

**Independent Test**: Can be fully tested by running the hook on classes that forward `**kwargs` to parent `__init__()` methods and verifying violations are detected.

**Acceptance Scenarios**:

1. **Given** a class with `__init__(self, **kwargs)` that calls `super().__init__(**kwargs)` where parent accepts no arguments, **When** the hook runs, **Then** a violation is detected and reported
2. **Given** a class that properly matches parent `__init__` signature, **When** the hook runs, **Then** no violation is detected
3. **Given** a class that forwards `**kwargs` to a parent that actually accepts `**kwargs`, **When** the hook runs, **Then** no violation is detected (legitimate use case)

---

### Edge Cases

- What happens when a file contains mixed violations (multiple hook types)?
- How does the hook handle files with syntax errors?
- What happens when a comment is already ambiguous in placement (could belong to multiple expressions)?
- How does the hook handle multi-line string literals that contain comment-like patterns?
- What happens when blank lines exist in the middle of the file (not after module headers)?
- How does the hook detect parent class signatures for super init checking when inheritance is complex (multiple inheritance, mixin patterns)?
- What happens when the parent class is imported from another module?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect trailing comments that appear on closing bracket lines (parentheses, square brackets, curly braces) where the opening bracket is on a different line
- **FR-002**: System MUST be able to move misplaced trailing comments to the correct position (either inline with the expression or as a preceding comment)
- **FR-003**: System MUST prefer inline comment placement when the expression line is short enough, otherwise use preceding comment format
- **FR-004**: System MUST detect runs of 2 or more consecutive blank lines immediately following module-level comments or docstrings
- **FR-005**: System MUST collapse multiple consecutive blank lines to a single blank line
- **FR-006**: System MUST preserve the required single blank line after copyright comments
- **FR-007**: System MUST detect class `__init__` methods that accept `**kwargs` and forward them to `super().__init__(**kwargs)`
- **FR-008**: System MUST determine if the parent class `__init__` signature accepts arguments or `**kwargs`
- **FR-009**: System MUST report a violation when `**kwargs` are forwarded to a parent `__init__` that accepts no arguments
- **FR-010**: Each hook MUST be independently executable (can run individually or as part of a suite)
- **FR-011**: Each hook MUST support both detection-only mode and auto-fix mode
- **FR-012**: Hooks MUST use only Python standard library (no external dependencies beyond what pre-commit provides)
- **FR-013**: Hooks MUST return exit code 0 when no violations found, non-zero when violations exist
- **FR-014**: Hooks MUST report clear, actionable error messages indicating file name, line number, and violation type
- **FR-015**: Auto-fix mode MUST preserve original file encoding and line ending style
- **FR-016**: Hooks MUST skip files with syntax errors and report them appropriately

### Key Entities

- **Hook Configuration**: Defines which hooks are enabled, their modes (detect vs fix), and any configuration options
- **Violation**: Represents a single detected issue with file path, line number, violation type, and suggested fix
- **File Context**: Represents the parsed structure of a Python file including AST, comments, blank lines, and class hierarchies
- **Comment Placement Rule**: Encodes the logic for determining correct comment placement (inline vs preceding)
- **Parent Signature**: Represents the `__init__` signature of parent classes for inheritance analysis

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can run all three hooks on their Python codebase and receive clear violation reports in under 5 seconds for codebases up to 10,000 lines
- **SC-002**: Auto-fix mode successfully corrects 95% of style violations without introducing syntax errors or changing code behavior
- **SC-003**: Hook error messages are clear enough that 90% of developers can understand and fix violations without consulting documentation
- **SC-004**: Hooks integrate seamlessly with pre-commit framework and can be installed using standard pre-commit configuration
- **SC-005**: False positive rate is below 5% (fewer than 1 in 20 reported violations are incorrect)
- **SC-006**: Hooks can analyze files with complex Python syntax including decorators, async/await, type hints, and f-strings without errors

## Assumptions *(mandatory)*

- Developers are using Python 3.8+ (minimum version supported by pre-commit framework)
- Code follows basic Python syntax rules (hooks may skip or error on files with syntax errors)
- For STYLE-001, we assume "short line" means the resulting line with inline comment would be ≤88 characters (Black's default line length)
- For STYLE-002, we assume module-level comments/docstrings are those appearing before the first import or class/function definition
- For MAINTAINABILITY-006, we assume parent class definitions are accessible for signature inspection (either in same file or importable)
- Developers want violations fixed automatically in most cases (auto-fix is preferred default behavior)
- The hooks will be run in a CI/CD environment where they should fail the build on violations
- Files use consistent encoding (UTF-8 is standard Python default)

## Constraints *(mandatory)*

- Must not introduce dependencies beyond Python standard library
- Must work with Python 3.8+ (cannot use Python 3.9+ only features)
- Must be compatible with pre-commit framework's execution model
- Must not modify files when run in detection-only mode
- Must complete analysis within reasonable time (no more than 1 second per 1000 lines of code)
- Must handle edge cases gracefully without crashing (e.g., syntax errors, unusual formatting)
- For MAINTAINABILITY-006, limited to analyzing parent classes defined in the same file or standard library (cannot analyze all possible imports)

## Dependencies *(optional)*

- **Python 3.8+**: Minimum runtime environment
- **pre-commit framework**: Hooks must be compatible with pre-commit's hook execution model and configuration format
- **Python AST module**: For parsing Python source code and analyzing class hierarchies
- **Python tokenize module**: For preserving comments and analyzing tokens
- **Python inspect module**: For analyzing parent class signatures (where accessible)

## Non-Goals *(optional)*

- This feature does NOT aim to replace comprehensive linters like Pylint or Flake8
- This feature does NOT aim to enforce all possible Python style guidelines (only the three specific rules)
- This feature does NOT aim to fix all code quality issues (focused on specific style and maintainability patterns)
- This feature does NOT aim to support languages other than Python
- This feature does NOT aim to provide IDE integration (works through pre-commit only)
- This feature does NOT aim to analyze parent classes defined in third-party packages (only same-file and standard library for MAINTAINABILITY-006)
- This feature does NOT aim to handle all possible AST edge cases (may skip complex or unusual code patterns)
