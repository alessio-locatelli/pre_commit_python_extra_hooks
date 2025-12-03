# CLI Interface Contract

## Overview

This document specifies the command-line interface for the two hooks being modified. **No changes** will be made to the CLI interface - this is a bug fix that maintains 100% backward compatibility.

## Hook: `fix-misplaced-comments`

### Command Signature

```bash
fix-misplaced-comments [--fix] [filenames...]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filenames` | positional, multiple | No | Paths to Python files to check/fix |
| `--fix` | flag | No | Automatically fix violations instead of just reporting them |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No violations found |
| 1 | Violations found (and optionally fixed) |

### Output Format

#### Check Mode (without `--fix`)

```
{filename}:{line_number}: STYLE-001: {message}
```

**Example**:
```
src/example.py:42: STYLE-001: Comment on line 43 should not be on closing bracket line
```

#### Fix Mode (with `--fix`)

```
Fixed: {filename}
```

**Example**:
```
Fixed: src/example.py
```

### Behavior Changes (Bug Fixes)

| Scenario | Old Behavior | New Behavior |
|----------|-------------|--------------|
| Linter pragma comments | Moved to previous line | Preserved on original line (not moved) |
| Bracket-only lines with comments | Sometimes incorrectly identified | Correctly identified using token analysis |
| Lines with code + brackets + comments | Sometimes moved | Never moved (stays on same line) |

### Examples

**Before fix (incorrect behavior)**:
```python
# Input
result = set()  # type: ignore

# After running hook (WRONG - breaks type checking)
# type: ignore
result = set()
```

**After fix (correct behavior)**:
```python
# Input
result = set()  # type: ignore

# After running hook (CORRECT - pragma preserved)
result = set()  # type: ignore
```

---

## Hook: `fix-excessive-blank-lines`

### Command Signature

```bash
fix-excessive-blank-lines [--fix] [filenames...]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filenames` | positional, multiple | No | Paths to Python files to check/fix |
| `--fix` | flag | No | Automatically fix violations instead of just reporting them |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No violations found |
| 1 | Violations found (and optionally fixed) |

### Output Format

#### Check Mode (without `--fix`)

```
{filename}:{line_number}: STYLE-002: Excessive blank lines ({count}) should be collapsed to 1
```

**Example**:
```
src/example.py:8: STYLE-002: Excessive blank lines (3) should be collapsed to 1
```

#### Fix Mode (with `--fix`)

```
Fixed: {filename}
```

**Example**:
```
Fixed: src/example.py
```

### Behavior Changes (Bug Fixes)

| Scenario | Old Behavior | New Behavior |
|----------|-------------|--------------|
| Blank lines between functions | Collapsed if 2+ consecutive | Preserved (not modified) |
| Blank lines in function bodies | Collapsed if 2+ consecutive | Preserved (not modified) |
| Blank lines between header and first code | Collapsed if 2+ consecutive | Collapsed if 2+ consecutive (same) |
| Files with no header | All blank lines checked | No blank lines modified |

### Scope Change

**Old behavior**: Scans entire file from header end to EOF
**New behavior**: Scans only from header end to first code line

### Examples

**Before fix (incorrect behavior)**:
```python
# Input
"""Module docstring."""


import os  # This is fine


def foo():
    pass


def bar():  # BUG: These intentional blanks were being collapsed
    pass
```

**After fix (correct behavior)**:
```python
# Input
"""Module docstring."""


import os

def foo():
    pass


def bar():  # Intentional blanks preserved
    pass
```

---

## Pre-commit Configuration

### `.pre-commit-config.yaml` Entry

**No changes required** - existing configurations continue to work:

```yaml
repos:
  - repo: https://github.com/your-org/pre_commit_extra_hooks
    rev: v0.0.1  # or later version with bug fixes
    hooks:
      - id: fix-misplaced-comments
      - id: fix-excessive-blank-lines
```

### Hook Definitions

Defined in `.pre-commit-hooks.yaml` at repository root (no changes):

```yaml
- id: fix-misplaced-comments
  name: Fix misplaced comments
  entry: fix-misplaced-comments
  language: python
  types: [python]

- id: fix-excessive-blank-lines
  name: Fix excessive blank lines
  entry: fix-excessive-blank-lines
  language: python
  types: [python]
```

---

## Backward Compatibility Guarantees

### ✅ Guaranteed Compatible

1. **Command-line arguments**: No changes to argument parsing
2. **Exit codes**: Same exit code semantics
3. **Output format**: Same message format for violations
4. **File handling**: Same error handling for invalid files
5. **Entry points**: Same module entry points

### ✅ Behavioral Improvements (Bug Fixes Only)

1. **Linter pragmas**: Now correctly preserved (fixes broken functionality)
2. **Bracket detection**: More accurate (reduces false positives)
3. **Blank line scope**: More targeted (prevents unintended changes)

### ❌ No Breaking Changes

1. No new required arguments
2. No removed functionality
3. No changed output formats
4. No new error conditions

---

## Testing Contract

### Test Expectations

Both hooks must:
1. Accept filenames via `sys.argv` or `argv` parameter
2. Return exit code 0 or 1
3. Write output to `sys.stderr`
4. Handle invalid Python syntax gracefully
5. Preserve file encoding
6. Use `--fix` flag to enable auto-fixing

### Error Handling

| Error Type | Behavior |
|------------|----------|
| Syntax error in Python file | Skip file, return empty violations |
| Unicode decode error | Skip file, return empty violations |
| File I/O error during read | Skip file, return empty violations |
| File I/O error during write | Skip file, suppress exception |

---

## Version Compatibility

- **Minimum Python version**: 3.13+ (as per constitution)
- **Standard library modules used**: `argparse`, `sys`, `tokenize`, `re`, `io`
- **No third-party dependencies**: Guaranteed by constitution
