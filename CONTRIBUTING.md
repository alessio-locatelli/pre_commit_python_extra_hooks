# Contributing to Pre-Commit Extra Hooks

Thank you for contributing to this project! This guide will help you add new hooks, update existing ones, and maintain the repository.

## Table of Contents

- [Getting Started](#getting-started)
- [Adding a New Hook](#adding-a-new-hook)
- [Updating Existing Hooks](#updating-existing-hooks)
- [Semantic Versioning](#semantic-versioning)
- [Backward Compatibility](#backward-compatibility)
- [Performance Testing](#performance-testing)
- [Release Process](#release-process)
- [CI/CD Configuration](#cicd-configuration)
- [Code Quality Standards](#code-quality-standards)

## Getting Started

### Prerequisites

- Python 3.8 or later
- Git
- pre-commit framework

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/pre-commit-extra-hooks.git
cd pre-commit-extra-hooks

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (dogfooding!)
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run tests for a specific hook
pytest tests/test_forbid_vars.py -v

# Run with coverage
pytest tests/ --cov=pre_commit_hooks --cov-report=html
```

### Run Linters

```bash
# Check code style
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check all pre-commit hooks
pre-commit run --all-files
```

## Adding a New Hook

Follow these steps to add a new hook to the repository:

### 1. Design Phase

Before writing code:

- Define the hook's purpose (single responsibility)
- Identify which file types it will check
- Decide what exit codes to use (0 = success, 1 = failure)
- Plan the error message format
- Consider configuration options (CLI arguments)
- **Choose the right implementation approach** (see below)

#### Choosing Between Bash and Python

**Constitution I (KISS Principle)** states: *"Prefer Bash + Git commands; fall back to Python only when necessary."*

Use this decision tree to choose the right tool:

##### ✅ Use Bash/Grep When:

The check is **pattern-based** and **context-independent**:

```bash
# ✓ Check for trailing whitespace
grep -n ' $' "$@"

# ✓ Check for TODO/FIXME comments
grep -n 'TODO\|FIXME' "$@"

# ✓ Check for hardcoded IPs
grep -E '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' "$@"

# ✓ Check for print() debugging statements
grep -n 'print(' "$@"

# ✓ Check for console.log in JavaScript
grep -n 'console\.log' "$@"

# ✓ Ensure files end with newline
for file in "$@"; do
    [ -n "$(tail -c 1 "$file")" ] && echo "$file: Missing final newline"
done
```

**Characteristics of bash-appropriate checks:**
- Simple string/regex matching
- No need to understand syntax context
- Pattern means the same thing everywhere
- No false positives from strings/comments/etc.
- No complex suppression logic needed

##### ⚠️ Use Python/AST When:

The check requires **syntax awareness** or **semantic understanding**:

```python
# ✗ CANNOT use bash reliably:

# Forbidden variable names (forbid-vars hook)
# - Must distinguish: data = 1  vs  obj.data = 1  vs  "data = 1"
# - Must detect function parameters: def foo(data):
# - Needs inline suppression logic

# Unused imports
# - Must parse import statements
# - Must track variable usage in scope

# Function complexity (too many parameters)
# - Must parse function signatures
# - Must handle *args, **kwargs

# Enforce type hints
# - Must understand Python syntax (def foo(x: int) -> str)
# - Must distinguish annotated from non-annotated functions
```

**Characteristics of Python-appropriate checks:**
- Requires parsing language syntax
- Context-dependent (same text means different things)
- Risk of false positives with simple grep
- Needs suppression via inline comments
- Requires accurate line number tracking

##### Real-World Example: Why forbid-vars Uses AST

**Bash/grep approach (WRONG):**

```bash
grep -E "\bdata =|\bresult =" *.py
```

**Problems:**

```python
# Test file
obj.data = 1                    # ❌ False positive (attribute, not variable)
user_data = 1                   # ❌ False positive (\b matches "user_data")
data = fetch()                  # ✓ Correct detection
def process(data):              # ❌ MISSED (function parameter not detected!)
    result = transform(data)    # ✓ Correct detection
    "data = 1"                  # ❌ False positive (inside string)
```

**Bash accuracy: ~50%** (1 false positive, 1 missed violation)

**Python/AST approach (CORRECT):**

```python
# Uses ast.NodeVisitor to check:
# - ast.Assign (data = 1)
# - ast.AnnAssign (data: int = 1)
# - ast.FunctionDef parameters (def foo(data):)
# - Filters out attributes, strings, comments automatically
```

**Python accuracy: 100%** (zero false positives, zero misses)

##### Decision Criteria Summary

| Question | Bash | Python |
|----------|------|--------|
| Simple string pattern? | ✓ | |
| Works in any context (strings, comments, code)? | ✓ | |
| Need to understand language syntax? | | ✓ |
| Need to distinguish variables vs attributes? | | ✓ |
| Need inline suppression logic? | | ✓ |
| Risk of false positives with grep? | | ✓ |
| Checking Python/JS/Go code structure? | | ✓ |

**When in doubt:** Start with bash. If you find false positives or missed violations in testing, switch to Python with proper parsing.

### 2. Create Hook Module

Create `pre_commit_hooks/your_hook.py`:

```python
"""Brief description of what this hook does."""

import argparse
import sys
from typing import Sequence


def check_file(filepath: str) -> list[str]:
    """
    Check a single file for violations.

    Args:
        filepath: Path to the file to check

    Returns:
        List of error messages (empty if no violations)
    """
    errors = []

    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Your validation logic here
        # ...

    except (OSError, UnicodeDecodeError):
        # Skip files we can't read
        return []

    return errors


def main(argv: Sequence[str] | None = None) -> int:
    """
    Main entry point for the hook.

    Args:
        argv: Command-line arguments

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    parser = argparse.ArgumentParser(description="Description of your hook")
    parser.add_argument("filenames", nargs="*", help="Filenames to check")
    # Add custom arguments as needed
    # parser.add_argument("--option", help="Description")

    args = parser.parse_args(argv)

    failed = False
    for filepath in args.filenames:
        errors = check_file(filepath)
        if errors:
            failed = True
            for error in errors:
                # Standard format: filepath:line: message
                print(error)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

**Key Requirements:**

- Use only Python standard library (no external dependencies)
- Accept file paths as positional arguments
- Return exit code 0 for success, non-zero for failure
- Print errors to stdout in format `filepath:line: message`
- Handle file read errors gracefully
- Support running without git/pre-commit (independence requirement)

### 3. Add Entry Point

Update `pyproject.toml` under `[project.scripts]`:

```toml
[project.scripts]
forbid-vars = "pre_commit_hooks.forbid_vars:main"
your-hook = "pre_commit_hooks.your_hook:main"  # Add this line
```

### 4. Update Hook Metadata

Add to `.pre-commit-hooks.yaml`:

```yaml
- id: your-hook
  name: brief description
  description: Longer description of what the hook does
  entry: your-hook
  language: python
  types: [python] # or other file types: [yaml], [markdown], etc.
  # Optional fields:
  # args: ['--default-arg=value']
  # require_serial: true  # if hook needs to run serially
```

### 5. Write Tests

Create `tests/test_your_hook.py`:

```python
"""Tests for your-hook."""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def run_hook(filenames, args=None):
    """Helper to run the hook."""
    cmd = [sys.executable, "-m", "pre_commit_hooks.your_hook"]
    if args:
        cmd.extend(args)
    cmd.extend(str(f) for f in filenames)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def test_success_case():
    """Test that valid files pass."""
    valid_file = FIXTURES_DIR / "valid.py"
    returncode, stdout, stderr = run_hook([valid_file])
    assert returncode == 0
    assert stdout == ""


def test_failure_case():
    """Test that invalid files fail with error messages."""
    invalid_file = FIXTURES_DIR / "invalid.py"
    returncode, stdout, stderr = run_hook([invalid_file])
    assert returncode == 1
    assert "expected error" in stdout
```

**Required Test Coverage:**

- Success cases (exit 0)
- Failure cases (exit 1 with error messages)
- Edge cases (empty files, binary files, syntax errors)
- CLI argument handling
- Independence (hook runs without git/pre-commit)

### 6. Create Test Fixtures

Create sample files in `tests/fixtures/`:

- `valid_<hookname>.py` - Files that should pass
- `invalid_<hookname>.py` - Files that should fail

### 7. Update Documentation

Add to `README.md`:

#### In "Available Hooks" section:

```markdown
### your-hook

Brief description of what the hook does.

**Features:**

- Feature 1
- Feature 2
```

#### In "Configuration Options" section:

```markdown
### your-hook

**Arguments:**

- `--option`: Description of option

**Example:**

```yaml
- id: your-hook
  args: ["--option=value"]
```
```

### 8. Test and Validate

```bash
# Run tests
pytest tests/test_your_hook.py -v

# Test hook independently
python -m pre_commit_hooks.your_hook tests/fixtures/invalid.py

# Run linter
ruff check pre_commit_hooks/your_hook.py

# Run all pre-commit hooks
pre-commit run --all-files
```

## Updating Existing Hooks

When updating an existing hook:

### 1. Maintain Backward Compatibility

- Don't remove CLI arguments (deprecate with warnings instead)
- Don't change default behavior in breaking ways
- Add new features as opt-in (via flags)
- Document migration path for breaking changes

### 2. Update Tests

- Add tests for new functionality
- Keep existing tests passing
- Update test fixtures if needed

### 3. Update Documentation

- Update README.md with new features
- Add migration notes if applicable
- Update CHANGELOG.md

### 4. Validate Changes

```bash
# Run full test suite
pytest tests/ -v

# Test manually on real files
python -m pre_commit_hooks.hook_name path/to/file.py

# Run linter
ruff check .
```

## Semantic Versioning

This repository follows [Semantic Versioning 2.0.0](https://semver.org/).

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR**: Incompatible API changes (breaking changes)
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

### Examples

**PATCH (1.0.0 → 1.0.1):**

- Fix bug in error message formatting
- Fix crash on edge case
- Performance improvement with no API changes

**MINOR (1.0.0 → 1.1.0):**

- Add new hook to repository
- Add new CLI argument to existing hook (opt-in)
- Add new file type support to hook

**MAJOR (1.0.0 → 2.0.0):**

- Remove deprecated CLI argument
- Change default forbidden names in forbid-vars
- Change error message format in breaking way
- Remove a hook entirely

### Deprecation Process

Before removing features (MAJOR version bump):

1. Mark feature as deprecated in MINOR version
2. Add deprecation warning to output
3. Document migration path in README and CHANGELOG
4. Wait at least one MINOR version before removal
5. Remove in next MAJOR version

**Example:**

```python
# v1.1.0: Add deprecation warning
if args.old_option:
    print("WARNING: --old-option is deprecated, use --new-option instead", file=sys.stderr)

# v2.0.0: Remove old option
# (old_option no longer accepted)
```

## Backward Compatibility

### Guidelines

1. **CLI Interface Stability:**
   - Hook IDs never change (e.g., `forbid-vars` is permanent)
   - New arguments are optional with sensible defaults
   - Deprecated arguments show warnings before removal

2. **Error Format Stability:**
   - Maintain `filepath:line: message` format
   - Tools may parse this format, don't break it

3. **Behavior Stability:**
   - Default configurations remain constant
   - New checks are opt-in via arguments
   - Exit codes remain: 0 (success), 1 (failure)

4. **Configuration Compatibility:**
   - `.pre-commit-hooks.yaml` schema remains stable
   - New fields are optional
   - Old configurations continue working

### Testing Backward Compatibility

```bash
# Test with minimal configuration (defaults only)
forbid-vars file.py

# Test with old argument syntax
forbid-vars --names=data,result file.py

# Verify exit codes
forbid-vars file.py && echo "EXIT 0" || echo "EXIT 1"
```

## Performance Testing

All hooks must meet performance requirements.

### Performance Target

**Requirement:** Process <1000 files in <5 seconds

### Benchmarking

Create a performance test:

```python
# tests/test_performance.py
import tempfile
import time
from pathlib import Path


def test_forbid_vars_performance():
    """Test that hook processes 1000 files in under 5 seconds."""
    # Create 1000 temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        for i in range(1000):
            filepath = Path(tmpdir) / f"file_{i}.py"
            filepath.write_text(f"x = {i}\n")
            files.append(str(filepath))

        # Measure execution time
        start = time.time()
        returncode = main(files)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Hook took {elapsed:.2f}s (should be <5s)"
        assert returncode == 0
```

### Profiling

Use Python profiling tools to identify bottlenecks:

```bash
# Profile hook execution
python -m cProfile -o profile.stats -m pre_commit_hooks.forbid_vars file.py

# View results
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

### Optimization Guidelines

1. **Minimize I/O:**
   - Read files once
   - Use buffered I/O
   - Skip binary files early

2. **Efficient Algorithms:**
   - Prefer O(n) over O(n²)
   - Use set lookups instead of list searches
   - Avoid regex when simple string operations suffice

3. **Lazy Evaluation:**
   - Parse only when necessary
   - Use generators for large datasets

4. **Parallel Processing:**
   - pre-commit runs hooks in parallel by default
   - Avoid `require_serial: true` unless necessary

## Release Process

### 1. Update Version

Update version in `pyproject.toml`:

```toml
[project]
version = "1.1.0"  # Increment according to semver
```

Update version in `pre_commit_hooks/__init__.py`:

```python
__version__ = "1.1.0"
```

### 2. Update CHANGELOG

Create or update `CHANGELOG.md`:

```markdown
# Changelog

## [1.1.0] - 2025-11-28

### Added

- New hook: check-docstrings
- forbid-vars: Added --custom-message argument

### Fixed

- forbid-vars: Fixed crash on empty function parameters

### Deprecated

- forbid-vars: --old-arg is deprecated, use --new-arg
```

### 3. Run Full Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run linters
pre-commit run --all-files

# Manual smoke test
python -m pre_commit_hooks.forbid_vars tests/fixtures/invalid_code.py
```

### 4. Create Git Tag

```bash
# Commit version changes
git add pyproject.toml pre_commit_hooks/__init__.py CHANGELOG.md
git commit -m "Bump version to v1.1.0"

# Create annotated tag
git tag -a v1.1.0 -m "Release v1.1.0"

# Push changes and tag
git push origin main
git push origin v1.1.0
```

### 5. Verify Release

Users can now use the new version:

```yaml
repos:
  - repo: https://github.com/YOUR_USERNAME/pre-commit-extra-hooks
    rev: v1.1.0 # New version
    hooks:
      - id: forbid-vars
```

Test autoupdate works:

```bash
pre-commit autoupdate
```

## CI/CD Configuration

### Recommended GitHub Actions

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run ruff
        run: ruff check .

      - name: Run tests
        run: pytest tests/ -v --cov=pre_commit_hooks

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - uses: pre-commit/action@v3.0.0
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
image: python:3.11

stages:
  - test
  - lint

test:
  stage: test
  script:
    - pip install -e ".[dev]"
    - pytest tests/ -v --cov=pre_commit_hooks
  coverage: '/TOTAL.*\s+(\d+%)$/'

lint:
  stage: lint
  script:
    - pip install ruff pre-commit
    - ruff check .
    - pre-commit run --all-files
```

## Code Quality Standards

### Python Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use f-strings for string formatting

### Docstrings

Use Google-style docstrings:

```python
def check_file(filepath: str, forbidden_names: set[str]) -> list[str]:
    """
    Check a Python file for forbidden variable names.

    Args:
        filepath: Path to the Python file to check
        forbidden_names: Set of forbidden variable names

    Returns:
        List of error messages (empty if no violations)

    Raises:
        OSError: If file cannot be read
    """
```

### Testing

- Aim for >90% code coverage
- Test success cases, failure cases, and edge cases
- Use descriptive test names: `test_what_when_expected`
- Include docstrings in tests explaining what they verify

### Error Messages

Format: `filepath:line: clear message`

**Good:**

```
src/app.py:42: Forbidden variable name 'data' found. Use a more descriptive name.
```

**Bad:**

```
Error in file (line 42)
```

## Questions?

If you have questions about contributing:

- Open an issue with the `question` label
- Check existing issues for similar questions
- Review the README.md for usage examples

Thank you for contributing! 🎉
