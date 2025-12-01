# Pre-Commit Extra Hooks

Custom pre-commit hooks for code quality enforcement.

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Python 3.13+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Available Hooks

---

### fix-misplaced-comments

**STYLE-001**: Automatically fixes trailing comments on closing brackets by moving them to the expression line.

**Why?** When auto-formatters move closing brackets to new lines, comments on those lines become orphaned and lose context.

**Example:**

```python
# Bad - comment is on bracket line:
result = func(
    arg
)  # Comment about the function call

# Fixed - comment moves to expression line:
result = func(
    arg  # Comment about the function call
)
```

**Features:**

- Automatically moves comments from closing bracket lines to expression lines
- Places comments inline if they fit within 88 characters
- Otherwise places them as preceding comments on their own line
- Preserves file encoding and line endings
- Gracefully handles syntax errors in source files

---

### fix-excessive-blank-lines

**STYLE-002**: Collapses multiple consecutive blank lines after module headers (copyright, docstrings, or comments) to a single blank line.

**Why?** Excessive blank lines after module headers create visual clutter and violate PEP 8 conventions.

**Example:**

```python
"""Module docstring."""



import os  # Bad - 3 blank lines

# Fixed:
"""Module docstring."""

import os  # Good - 1 blank line
```

**Features:**

- Detects 2+ blank lines after module header
- Preserves copyright comment spacing (1 blank line after copyright)
- Only affects module-level blank lines, preserves function/class spacing
- Maintains file encoding and handles different line ending styles

---

### check-redundant-super-init

**MAINTAINABILITY-006**: Detects when a class forwards `**kwargs` to a parent `__init__` that accepts no arguments.

**Why?** Forwarding kwargs to parents that don't accept them is a logic error that creates misleading inheritance patterns.

**Example:**

```python
# Bad - redundant kwargs forwarding:
class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # VIOLATION: Base doesn't accept kwargs

# Fixed - matching signatures:
class Child(Base):
    def __init__(self):
        super().__init__()
```

**Features:**

- Detects redundant `**kwargs` forwarding using AST analysis
- Analyzes class hierarchies and method signatures
- Limited to same-file parent classes (safe, zero false positives)
- Handles multiple inheritance correctly
- Gracefully skips unresolvable parent classes (imports, stdlib)

---

### forbid-vars

Prevents use of meaningless variable names like `data` and `result`. Now with autofix!

**Why?** Meaningless variable names reduce code clarity and maintainability. See [Peter Hilton's article on meaningless variable names](https://hilton.org.uk/blog/meaningless-variable-names) for more context.

**Default forbidden names:**

- `data`
- `result`

**Features:**

- Detects forbidden names in assignments, function parameters, and async functions
- **Autofixing**: Suggests and optionally applies meaningful names based on context (`--fix`).
- Supports custom blacklist via `--names` argument
- Inline suppression with `# maintainability: ignore[meaningless-variable-name]`
- Clear error messages with line numbers and helpful links
- Works independently (no git/pre-commit required for testing)

#### Autofixing Violations

The `forbid-vars` hook can now automatically suggest and apply fixes for common violation patterns.

**Suggest Mode (default):**

By default, the hook runs in "suggest mode". It will report forbidden names and suggest a better name if a known pattern is matched.

```
src/process.py:42: Forbidden variable name 'data' found. Consider renaming to 'user_records'. Or add ...
```

**Fix Mode (`--fix`):**

To automatically apply the suggested fixes, you can use the `--fix` argument in your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/YOUR_USERNAME/pre-commit-extra-hooks
  rev: v1.0.0
  hooks:
    - id: forbid-vars
      args: ["--fix"]
```

When a fix is applied, the hook will report the change:

```
Applied fix for 'data' -> 'user_records' in src/process.py:42
```

#### Autofix Configuration (`pyproject.toml`)

You can configure the autofix behavior in your `pyproject.toml` file.

**Enabling/Disabling Categories:**

The autofix patterns are grouped into categories (`http`, `file`, `database`, `data-science`, `semantic`). By default, only the `http` category is enabled. You can enable more categories like this:

```toml
[tool.forbid-vars.autofix]
enabled = ["http", "file", "database"]
```

**Custom Patterns:**

You can also add your own custom patterns. This is useful for project-specific conventions.

```toml
[tool.forbid-vars.autofix]
enabled = ["custom"]

[[tool.forbid-vars.autofix.patterns]]
category = "custom"
regex = "get_user_profile"
name = "user_profile"
```

**Limitation:** The autofix feature performs a file-wide search and replace for the variable name. This works well in most cases, but it can lead to incorrect changes if the same forbidden variable name (e.g., `data`) is used for different things in the same file. It is recommended to avoid reusing generic names for different purposes within the same file.

---

### fix-misplaced-comments

### Using pre-commit

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/YOUR_USERNAME/pre-commit-extra-hooks
    rev: v1.0.0 # Use the latest version tag
    hooks:
      - id: forbid-vars
```

Then install the pre-commit hooks:

```bash
pre-commit install
```

### Manual Installation

```bash
pip install git+https://github.com/YOUR_USERNAME/pre-commit-extra-hooks.git
```

## Usage

### Automatic (via pre-commit)

Once installed, the hook runs automatically on `git commit`:

```bash
git add .
git commit -m "Add new feature"
```

**Example output when violations are found:**

```
forbid meaningless variable names...............................Failed
- hook id: forbid-vars
- exit code: 1

src/process.py:42: Forbidden variable name 'data' found. Use a more descriptive name or add '# maintainability: ignore[meaningless-variable-name]' to suppress. See https://hilton.org.uk/blog/meaningless-variable-names
```

### Manual Execution

Run the hook manually on specific files:

```bash
pre-commit run forbid-vars --all-files
```

Run the hook directly (independent of pre-commit):

```bash
forbid-vars src/main.py src/utils.py
```

## Configuration

### Custom Forbidden Names

Override the default blacklist with your own:

```yaml
- repo: https://github.com/YOUR_USERNAME/pre-commit-extra-hooks
  rev: v1.0.0
  hooks:
    - id: forbid-vars
      args: ["--names=data,result,info,temp,obj,value"]
```

### Inline Suppression

Suppress violations on specific lines:

```python
# This will trigger a violation:
data = load_from_database()

# This will be ignored:
data = load_from_database()  # maintainability: ignore[meaningless-variable-name]
```

**Note:** The ignore comment must be on the same line as the violation.

## Examples

### ❌ Code that Fails

```python
def process():
    """Process data."""
    data = fetch()  # Violation: 'data' is forbidden
    result = transform(data)  # Violation: 'result' is forbidden
    return result


def calculate(data):  # Violation: parameter 'data'
    """Calculate something."""
    return data * 2
```

### ✅ Code that Passes

```python
def process_user_records():
    """Process user records."""
    user_records = fetch_users()
    transformed_output = transform(user_records)
    return transformed_output


def calculate_total(invoice_items):
    """Calculate total from invoice items."""
    return sum(item.price * item.quantity for item in invoice_items)
```

### ✅ Code with Suppression

```python
def legacy_code():
    """Legacy code with necessary suppressions."""
    # New code - descriptive names
    user_records = fetch_users()

    # Legacy code - suppressed (refactoring is risky)
    data = transform(user_records)  # maintainability: ignore[meaningless-variable-name]
    result = validate(data)  # maintainability: ignore[meaningless-variable-name]

    return result
```

## Adding New Hooks

Want to contribute a new hook to this repository? Follow these steps:

### 1. Create the Hook Script

Create a new Python module in `pre_commit_hooks/`:

```bash
touch pre_commit_hooks/your_hook.py
```

### 2. Implement the Hook

Your hook should:

- Accept file paths as command-line arguments
- Return exit code 0 for success, non-zero for failure
- Print error messages to stdout (format: `filepath:line: message`)
- Use only Python standard library (no external dependencies)

**Template:**

```python
"""Your hook description."""

import argparse
import sys
from typing import Sequence


def check_file(filepath: str) -> int:
    """Check a single file. Returns 0 for pass, 1 for fail."""
    # Your validation logic here
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Your hook description")
    parser.add_argument("filenames", nargs="*", help="Filenames to check")

    args = parser.parse_args(argv)

    failed = False
    for filepath in args.filenames:
        if check_file(filepath) != 0:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

### 3. Add Entry Point

Add to `pyproject.toml` under `[project.scripts]`:

```toml
[project.scripts]
your-hook = "pre_commit_hooks.your_hook:main"
```

### 4. Update Hook Metadata

Add to `.pre-commit-hooks.yaml`:

```yaml
- id: your-hook
  name: your hook name
  description: Your hook description
  entry: your-hook
  language: python
  types: [python] # or other file types
```

### 5. Write Tests

Create `tests/test_your_hook.py`:

```python
"""Tests for your-hook."""

import subprocess
import sys


def test_success_case():
    """Test that hook passes on valid files."""
    result = subprocess.run(
        [sys.executable, "-m", "pre_commit_hooks.your_hook", "tests/fixtures/valid.py"],
        capture_output=True,
    )
    assert result.returncode == 0
```

### 6. Test Independently

Your hook should work without git or pre-commit:

```bash
python -m pre_commit_hooks.your_hook path/to/file.py
```

## Testing Hooks

### Run Tests

```bash
pytest tests/
```

### Test a Specific Hook

```bash
pytest tests/test_forbid_vars.py -v
```

### Test Hook Independently

Run the hook directly to verify it works without pre-commit:

```bash
python -m pre_commit_hooks.forbid_vars tests/fixtures/invalid_code.py
```

## Configuration Options

### forbid-vars

**Arguments:**

- `--names`: Comma-separated list of forbidden variable names (default: `data,result`)

**Example:**

```yaml
- id: forbid-vars
  args: ["--names=data,result,info,temp"]
```

**Inline ignore pattern:**

```python
# maintainability: ignore[meaningless-variable-name]
```

(Case-insensitive, must be on same line as violation)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/pre-commit-extra-hooks.git
cd pre-commit-extra-hooks

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (dogfooding!)
pre-commit install
```

### Run Linter

```bash
ruff check .
ruff format .
```

### Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```text
pre-commit-extra-hooks/
├── .pre-commit-hooks.yaml   # Hook definitions
├── .pre-commit-config.yaml  # Self-dogfooding configuration
├── README.md                # This file
├── LICENSE                  # MIT license
├── pyproject.toml           # Python project metadata
│
├── pre_commit_hooks/        # Hook implementations
│   ├── __init__.py
│   └── forbid_vars.py       # forbid-vars hook
│
└── tests/                   # Test suite
    ├── __init__.py
    ├── test_forbid_vars.py
    └── fixtures/            # Test data
        ├── valid_code.py
        ├── invalid_code.py
        └── ignored_code.py
```

## Troubleshooting

### Hook not running

**Problem:** Hook doesn't run on commit.

**Solution:** Make sure you've installed the git hooks:

```bash
pre-commit install
```

### No violations reported despite bad code

**Problem:** Code with `data` variable passes the hook.

**Solution:** Check if:

1. File is a Python file (hook only runs on `*.py` files)
2. Inline ignore comment is present
3. The variable is actually being assigned (not an attribute like `obj.data`)

### Syntax errors in code

**Problem:** Hook fails on syntactically invalid Python.

**Solution:** The hook requires valid Python syntax to parse the AST. Fix syntax errors first:

```bash
python -m py_compile src/file.py
```

## License

MIT License. See [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding hooks and maintaining this repository.

## Resources

- [Pre-commit Framework](https://pre-commit.com/)
- [Meaningless Variable Names](https://hilton.org.uk/blog/meaningless-variable-names)
- [Python AST Documentation](https://docs.python.org/3/library/ast.html)
