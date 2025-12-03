# Quickstart Guide: Bug Fixes for Pre-commit Hooks

## What Changed?

This release fixes three critical bugs in the `fix-misplaced-comments` and `fix-excessive-blank-lines` hooks. **No changes are required to your `.pre-commit-config.yaml`** - just update to the latest version.

## For End Users

### Update Your Hooks

1. Update your `.pre-commit-config.yaml` to the latest version:

```yaml
repos:
  - repo: https://github.com/your-org/pre_commit_extra_hooks
    rev: v0.0.2  # Update to version with bug fixes
    hooks:
      - id: fix-misplaced-comments
      - id: fix-excessive-blank-lines
```

2. Run pre-commit to see the improvements:

```bash
pre-commit run --all-files
```

### What You'll Notice

#### Fix 1: Linter Pragmas Preserved

**Before (Broken)**:
```python
# Your code with pragmas got mangled:
# type: ignore
result = set()
```

**After (Fixed)**:
```python
# Pragmas stay where they belong:
result = set()  # type: ignore
```

Affected pragmas:
- `# noqa` (flake8, ruff)
- `# type: ignore` (mypy, pyright)
- `# pragma: no cover` (coverage.py)
- `# pylint:`, `# mypy:`, `# ruff:`, etc.

#### Fix 2: Smarter Bracket Detection

**Before (Broken)**:
```python
# Comments on lines with code got moved incorrectly
# Comment about set
synonyms: set[str] = set()
```

**After (Fixed)**:
```python
# Comments on code+bracket lines stay put:
synonyms: set[str] = set()  # Comment about set
```

Only comments on **bracket-only lines** get moved:
```python
result = func(
    arg1,
    arg2,
)  # This comment is moved
```

#### Fix 3: Intentional Spacing Preserved

**Before (Broken)**:
```python
def foo():
    pass
def bar():  # Your intentional blank was removed
    pass
```

**After (Fixed)**:
```python
def foo():
    pass

def bar():  # Blank preserved for readability
    pass
```

The hook now only cleans up spacing between file headers and code, not throughout the entire file.

---

## For Developers

### Running Tests

After pulling the bug fixes:

```bash
# Run all tests
uv run pytest

# Run specific hook tests
uv run pytest tests/test_fix_misplaced_comments.py
uv run pytest tests/test_fix_excessive_blank_lines.py

# Run with coverage
uv run pytest --cov=src/pre_commit_hooks
```

### Testing the Hooks Manually

#### Test `fix-misplaced-comments`

```bash
# Check mode (show violations)
uv run python -m pre_commit_hooks.fix_misplaced_comments test_file.py

# Fix mode (auto-fix violations)
uv run python -m pre_commit_hooks.fix_misplaced_comments --fix test_file.py
```

#### Test `fix-excessive-blank-lines`

```bash
# Check mode
uv run python -m pre_commit_hooks.fix_excessive_blank_lines test_file.py

# Fix mode
uv run python -m pre_commit_hooks.fix_excessive_blank_lines --fix test_file.py
```

### New Test Fixtures

The bug fixes include comprehensive test coverage:

```
tests/fixtures/
├── misplaced_comments/
│   ├── bad/
│   │   ├── ignore_comments.py    # NEW: Tests linter pragma preservation
│   │   └── bracket_comments.py   # NEW: Tests bracket-only detection
│   └── good/
│       ├── ignore_comments.py
│       └── bracket_comments.py
└── excessive_blank_lines/
    ├── bad/
    │   └── header_spacing.py     # NEW: Tests header-only scope
    └── good/
        └── header_spacing.py
```

### Implementation Details

#### Bug 1: Linter Pragma Blacklist

```python
LINTER_PRAGMA_PATTERNS = [
    r'#\s*noqa',
    r'#\s*type:\s*ignore',
    r'#\s*pragma:',
    # ... more patterns
]

def is_linter_pragma(comment_text: str) -> bool:
    return any(re.search(pattern, comment_text)
               for pattern in LINTER_PRAGMA_PATTERNS)
```

Comments matching these patterns are **never moved**.

#### Bug 2: Token-Based Bracket Detection

```python
def is_bracket_only_line(tokens: list, bracket_token_idx: int) -> bool:
    # Uses tokenize module to check if line has only brackets
    # More reliable than string parsing
```

Only lines with **exclusively brackets** (no other code) trigger comment movement.

#### Bug 3: Scoped Blank Line Processing

```python
# Old: Processed entire file
for i in range(header_end, len(lines)):
    # Collapsed all blanks

# New: Only process header → first code line
first_code_line = find_first_code_after_header(lines, header_end)
for i in range(header_end, first_code_line):
    # Collapse only header blanks
```

Blank lines in function bodies and between functions are **preserved**.

---

## Backward Compatibility

### ✅ 100% Compatible

- **CLI arguments**: No changes
- **Exit codes**: Same behavior
- **Output format**: Same violation messages
- **Configuration**: `.pre-commit-config.yaml` works as-is

### ✅ Behavioral Improvements Only

The changes are **exclusively bug fixes**:
1. Pragmas that were broken now work
2. Bracket detection is more accurate
3. Intentional spacing is preserved

**No valid use cases are broken** - only incorrect behavior is fixed.

---

## Migration Checklist

- [ ] Update `rev:` in `.pre-commit-config.yaml` to the latest version
- [ ] Run `pre-commit run --all-files` to verify behavior
- [ ] (Optional) Review any files that were previously modified incorrectly
- [ ] (Optional) Re-run hooks on previously broken files to fix them

**Estimated migration time**: < 5 minutes

---

## Common Scenarios

### Scenario 1: My linter pragmas were moved incorrectly

**Before**: Pre-commit hook broke `# noqa` comments, causing lint failures in CI.

**After**: Pragmas stay on their original lines, linters work correctly.

**Action**: Update to latest version, run `pre-commit run --all-files`.

---

### Scenario 2: My code formatting was changed unexpectedly

**Before**: The hook moved comments from lines like `result = set()  # Comment`.

**After**: Comments on lines with code are **never moved**, only comments on bracket-only lines.

**Action**: Update to latest version, review any previously mangled files.

---

### Scenario 3: My intentional blank lines were removed

**Before**: Blank lines between functions were collapsed against my coding style.

**After**: Only header-to-code blanks are modified, function spacing is preserved.

**Action**: Update to latest version, reformat files if needed.

---

## Reporting Issues

If you encounter unexpected behavior after updating:

1. Check that you're using the correct version (run `pre-commit --version`)
2. Review the [CLI Interface Contract](./contracts/cli-interface.md) for expected behavior
3. Create a minimal reproduction case
4. Open an issue with:
   - Input file content
   - Expected output
   - Actual output
   - Hook version and Python version

---

## Summary

**TL;DR**:
- Update your `.pre-commit-config.yaml` to the latest version
- No other changes needed
- Linter pragmas, bracket detection, and blank line handling now work correctly
- 100% backward compatible - only bug fixes, no breaking changes
