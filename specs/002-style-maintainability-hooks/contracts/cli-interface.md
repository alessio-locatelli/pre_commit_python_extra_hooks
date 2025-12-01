# CLI Interface Contracts

**Feature**: 002-style-maintainability-hooks
**Date**: 2025-11-30
**Purpose**: Define command-line interface contracts for all three hooks

## Overview

All three hooks follow the same CLI interface pattern compatible with pre-commit framework.

## Common Interface

### Command Pattern

```bash
python -m pre_commit_hooks.<hook_name> [--fix] [--] file1.py file2.py ...
```

### Arguments

| Argument    | Type       | Required | Default | Description                                    |
| ----------- | ---------- | -------- | ------- | ---------------------------------------------- |
| `filenames` | positional | Yes      | N/A     | One or more Python files to check              |
| `--fix`     | flag       | No       | False   | Enable auto-fix mode (modifies files in-place) |

### Exit Codes

| Code | Meaning                | When Returned                                                     |
| ---- | ---------------------- | ----------------------------------------------------------------- |
| 0    | Success                | No violations found                                               |
| 1    | Violations found/fixed | At least one violation detected or fixed                          |
| 2+   | Error                  | Unexpected error (should be rare; hooks handle errors gracefully) |

### Output Format

**Success (no violations)**:

```
(no output to stdout/stderr)
exit code: 0
```

**Violations detected (without --fix)**:

```
# To stderr:
src/example.py:15: STYLE-001: Comment on closing bracket should be moved to expression line
src/example.py:42: STYLE-001: Trailing comment on line with only ')', consider inline or preceding comment
src/other.py:8: STYLE-002: Found 3 consecutive blank lines after module header, should be 1

exit code: 1
```

**Violations fixed (with --fix)**:

```
# To stderr:
Fixed: src/example.py (2 issues)
Fixed: src/other.py (1 issue)

exit code: 1
```

**Syntax error (graceful handling)**:

```
# To stderr:
src/broken.py: Syntax error, skipping

exit code: 0  # Don't fail the hook on syntax errors
```

### Error Message Format

```
<filename>:<line>: <violation-type>: <message>
```

Components:

- `<filename>`: Relative or absolute path to file
- `<line>`: Line number (1-indexed)
- `<violation-type>`: One of "STYLE-001", "STYLE-002", "MAINTAINABILITY-006"
- `<message>`: Human-readable description with actionable guidance

## Hook-Specific Contracts

### 1. fix-misplaced-comments (STYLE-001)

**Module**: `pre_commit_hooks.fix_misplaced_comments`

**Purpose**: Detect and fix trailing comments on closing bracket lines

**Command**:

```bash
python -m pre_commit_hooks.fix_misplaced_comments [--fix] file1.py file2.py
```

**Behavior**:

- **Without --fix**: Reports violations, does not modify files
- **With --fix**: Modifies files in-place, moves comments to correct lines

**Detection Logic**:

- Scans for comments that appear on lines containing only closing brackets: `)`, `]`, `}`
- Considers a line "only closing bracket" if it has closing bracket + optional whitespace + comment

**Fix Logic**:

- Determines target line (the line with actual expression content)
- If target line + inline comment <= 88 chars: places comment inline
- Otherwise: places comment as preceding `#` comment on line above expression

**Example Violations**:

```python
# Input (bad):
result = some_function(
    arg1,
    arg2
)  # This comment is orphaned

# Output with --fix (good):
result = some_function(
    arg1,
    arg2  # This comment is now inline
)
```

**Edge Cases**:

- Multiple comments on same line: Kept together
- Comments in string literals: Ignored (not actual comments)
- Nested brackets: Each closing bracket handled independently

### 2. fix-excessive-blank-lines (STYLE-002)

**Module**: `pre_commit_hooks.fix_excessive_blank_lines`

**Purpose**: Detect and collapse excessive blank lines after module headers

**Command**:

```bash
python -m pre_commit_hooks.fix_excessive_blank_lines [--fix] file1.py file2.py
```

**Behavior**:

- **Without --fix**: Reports violations, does not modify files
- **With --fix**: Modifies files in-place, collapses blank lines to 1

**Detection Logic**:

- Identifies module header (shebang, encoding, module docstring, top-level comments)
- Finds end of module header (first import, class, def, or assignment)
- Scans for runs of 2+ consecutive blank lines immediately after header
- Special case: Copyright comments require exactly 1 blank line separator

**Fix Logic**:

- Collapses runs of 2+ blank lines to exactly 1 blank line
- Preserves 1 blank line after copyright comments
- Does not modify blank lines in the middle of the file (only after module header)

**Example Violations**:

```python
# Input (bad):
"""Module docstring."""


from something import foo

# Output with --fix (good):
"""Module docstring."""

from something import foo
```

**Edge Cases**:

- Copyright comment detection: Looks for `# Copyright`, `# (c)`, `# ©`
- Module docstring: Triple-quoted string before any code
- No module header: If file starts with code, no blank line collapsing

### 3. check-redundant-super-init (MAINTAINABILITY-006)

**Module**: `pre_commit_hooks.check_redundant_super_init`

**Purpose**: Detect redundant \*\*kwargs forwarding to parent **init** that accepts no arguments

**Command**:

```bash
python -m pre_commit_hooks.check_redundant_super_init file1.py file2.py
```

**Behavior**:

- **Detection-only hook** (no --fix flag support)
- Reports violations, does not modify files

**Detection Logic**:

- Parses file into AST
- Finds classes with **init** methods that accept \*\*kwargs
- Identifies super().**init**(\*\*kwargs) calls
- Attempts to resolve parent class **init** signature (same-file or stdlib)
- If parent **init** accepts no arguments beyond self, reports violation

**Fix Guidance** (manual):

- Remove \*\*kwargs from child **init** signature
- Change super().**init**(\*\*kwargs) to super().**init**()

**Example Violations**:

```python
# Input (violation):
class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self, **kwargs):  # **kwargs not needed
        super().__init__(**kwargs)  # Parent accepts no args
        self.x = 1

# Suggested fix:
class Child(Base):
    def __init__(self):
        super().__init__()
        self.x = 1
```

**Edge Cases**:

- Parent class not in same file: Skip (cannot resolve)
- Parent class from stdlib: Skip (most stdlib **init** accept args)
- Multiple inheritance: Check all parent classes, report if any mismatch
- Parent class accepts \*\*kwargs: No violation (legitimate forwarding)

## Pre-commit Configuration

All hooks will be registered in `.pre-commit-hooks.yaml`:

```yaml
- id: fix-misplaced-comments
  name: Fix misplaced comments
  description: Move trailing comments on closing brackets to expression lines
  entry: python -m pre_commit_hooks.fix_misplaced_comments
  language: python
  types: [python]
  args: [--fix] # Default to auto-fix mode

- id: fix-excessive-blank-lines
  name: Fix excessive blank lines
  description: Collapse multiple blank lines after module headers to one
  entry: python -m pre_commit_hooks.fix_excessive_blank_lines
  language: python
  types: [python]
  args: [--fix] # Default to auto-fix mode

- id: check-redundant-super-init
  name: Check redundant super init kwargs
  description: Detect redundant **kwargs forwarding to parent __init__()
  entry: python -m pre_commit_hooks.check_redundant_super_init
  language: python
  types: [python]
  # No --fix flag (detection-only hook)
```

## Integration Example

Users add to their `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/user/pre_commit_extra_hooks
    rev: v1.0.0
    hooks:
      - id: fix-misplaced-comments
      - id: fix-excessive-blank-lines
      - id: check-redundant-super-init
```

## Testing Contracts

Each hook must pass these test scenarios:

### Success Cases (exit 0)

- Clean files with no violations
- Empty files
- Files with already-correct formatting

### Failure Cases (exit 1)

- Files with violations (without --fix)
- Files that were fixed (with --fix)

### Error Cases (graceful handling)

- Files with syntax errors (skip, don't fail hook)
- Binary files (skip)
- Non-existent files (report error, don't crash)

### Edge Cases

- Very large files (10,000+ lines)
- Files with unusual encodings (UTF-16, etc.)
- Files with CRLF line endings (Windows)
- Files with mixed indentation
