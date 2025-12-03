# Feature Specification: Fix Reported Bugs in Pre-commit Hooks

**Feature Branch**: `004-fix-reported-bugs`
**Created**: 2025-12-01
**Status**: Draft
**Input**: User description: "Fix bugs in fix-misplaced-comments and fix-excessive-blank-lines hooks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve Linter Ignore Comments (Priority: P1)

Developers use linter ignore comments (`# noqa`, `# type: ignore`, `# pragma: no cover`, etc.) to suppress specific warnings. The `fix-misplaced-comments` hook currently moves these comments to different lines, breaking their association with the code they're meant to affect and causing linter warnings to reappear incorrectly.

**Why this priority**: This is the most critical bug because it breaks existing linter configurations and can cause false positives in CI/CD pipelines, blocking legitimate code from merging.

**Independent Test**: Can be fully tested by running the hook on Python files containing various linter ignore comments and verifying that these comments remain on their original lines and continue to suppress the intended warnings.

**Acceptance Scenarios**:

1. **Given** a Python file with a `# noqa` comment on a line with code, **When** the `fix-misplaced-comments` hook runs, **Then** the comment remains on the same line
2. **Given** a Python file with a `# type: ignore` comment, **When** the hook runs, **Then** the type checker still recognizes the ignore directive
3. **Given** a Python file with a `# pragma: no cover` comment, **When** the hook runs, **Then** the coverage tool still excludes that line from coverage analysis

---

### User Story 2 - Correctly Handle Comments on Bracket-Only Lines (Priority: P2)

When code has a comment on a line containing only closing brackets (parentheses, braces, or square brackets), the `fix-misplaced-comments` hook incorrectly moves the comment to a different line. This changes the intended meaning of the comment and can confuse developers reading the code.

**Why this priority**: While less critical than breaking linter directives, this bug still produces incorrect code transformations that alter developer intent and code readability.

**Independent Test**: Can be fully tested by running the hook on Python files with comments on bracket-only lines and verifying that the comments are moved to the appropriate preceding code line (not left in place or moved elsewhere incorrectly).

**Acceptance Scenarios**:

1. **Given** a Python file with a comment on a line containing only `)`, **When** the hook runs, **Then** the comment is moved to the line containing the actual code (not the bracket)
2. **Given** a Python file with a comment on a line containing only `}` or `]`, **When** the hook runs, **Then** the comment is moved appropriately
3. **Given** a Python file with a comment on a line containing both code and closing brackets, **When** the hook runs, **Then** the comment remains on that line

---

### User Story 3 - Scope Blank Line Collapse to File Headers (Priority: P3)

The `fix-excessive-blank-lines` hook currently collapses all consecutive blank lines throughout the entire file, but it should only target the spacing between top-level file headers (copyright, license comments) and the first line of actual code. Excessive blank lines elsewhere in the file may be intentional for readability.

**Why this priority**: This is the lowest priority because it's a scope issue rather than a correctness bug. The hook is overly aggressive but doesn't break functionality.

**Independent Test**: Can be fully tested by running the hook on Python files with various blank line patterns and verifying that only blank lines between the file header and first code statement are collapsed, while blank lines elsewhere remain unchanged.

**Acceptance Scenarios**:

1. **Given** a Python file with 5 blank lines between a copyright header and the first import statement, **When** the hook runs, **Then** the blank lines are reduced to 1
2. **Given** a Python file with 5 blank lines between two function definitions, **When** the hook runs, **Then** those blank lines remain unchanged
3. **Given** a Python file with no top-level header comments, **When** the hook runs, **Then** no blank lines are modified anywhere in the file

---

### Edge Cases

- What happens when a file contains multiple types of ignore comments on the same line (e.g., `# noqa # type: ignore`)?
- How does the system handle comments on lines with mixed opening and closing brackets (e.g., `)])`)?
- What happens when a file has no header comments at all (blank lines should not be modified)?
- How does the system distinguish between a file header comment block and other top-level comments?
- What happens with files that use non-standard comment formats or international characters in comments?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `fix-misplaced-comments` hook MUST NOT move any line containing linter ignore directives (including but not limited to: `# noqa`, `# type: ignore`, `# pragma`, `# pylint:`, `# mypy:`, `# pyright:`, `# flake8:`, `# ruff:`, `# bandit:`)
- **FR-002**: The `fix-misplaced-comments` hook MUST correctly identify lines containing only closing brackets (parentheses, braces, or square brackets) with optional whitespace
- **FR-003**: The `fix-misplaced-comments` hook MUST move comments from bracket-only lines to the appropriate preceding code line
- **FR-004**: The `fix-misplaced-comments` hook MUST NOT move comments from lines that contain both code and closing brackets
- **FR-005**: The `fix-excessive-blank-lines` hook MUST only collapse excessive blank lines in the region between the file header comment block and the first line of code
- **FR-006**: The `fix-excessive-blank-lines` hook MUST NOT modify blank lines elsewhere in the file (between functions, classes, or other code blocks)
- **FR-007**: The `fix-excessive-blank-lines` hook MUST correctly identify the end of the file header comment block (consecutive comment lines at the start of the file)
- **FR-008**: The `fix-excessive-blank-lines` hook MUST correctly identify the first line of actual code (first non-comment, non-blank line after the header)
- **FR-009**: All hooks MUST maintain backward compatibility with existing `.pre-commit-config.yaml` configurations

### Key Entities

- **Linter Ignore Comment**: A comment containing directives that suppress linter warnings for specific lines or blocks of code. Key attributes: comment text, line number, associated linter tool.
- **Bracket-Only Line**: A line containing only closing brackets (one or more of: `)`, `}`, `]`) with optional whitespace and an optional comment. Key attributes: bracket type(s), presence of comment.
- **File Header Comment Block**: Consecutive comment lines at the beginning of a file, typically containing copyright notices, license information, or module documentation. Key attributes: start line, end line, comment content.
- **Code Line**: A non-comment, non-blank line containing executable Python code. Key attributes: line number, code content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing test files with linter ignore comments pass their linter checks after the hook runs (0% increase in false positives)
- **SC-002**: Comments on bracket-only lines are correctly repositioned in 100% of test cases
- **SC-003**: The `fix-excessive-blank-lines` hook only modifies the header region and does not alter blank lines in the rest of the file in 100% of test cases
- **SC-004**: All existing pre-commit configurations continue to work without modification after the bug fixes are applied (100% backward compatibility)
- **SC-005**: The test suite covers all three bug scenarios and all identified edge cases with passing tests
