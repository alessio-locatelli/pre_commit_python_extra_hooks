# Quickstart Guide: Pre-Commit Extra Hooks

This guide helps you quickly set up and use the forbid-vars hook in your project.

## Prerequisites

- Python 3.8 or later
- Git repository
- pre-commit framework installed

## Installation

### 1. Install pre-commit (if not already installed)

```bash
# Using pip
pip install pre-commit

# Using homebrew (macOS)
brew install pre-commit

# Verify installation
pre-commit --version
```

### 2. Add hook to your project

Create or update `.pre-commit-config.yaml` in your repository root:

```yaml
repos:
  - repo: https://github.com/<user>/pre-commit-extra-hooks
    rev: v1.0.0 # Use the latest version
    hooks:
      - id: forbid-vars
```

### 3. Install the pre-commit hooks

```bash
pre-commit install
```

This sets up git hooks to run automatically on `git commit`.

## Usage

### Running Automatically on Commit

Once installed, the hook runs automatically when you commit:

```bash
git add .
git commit -m "Add new feature"
```

**If violations are found:**

```
forbid meaningless variable names...............................Failed
- hook id: forbid-vars
- exit code: 1

src/process.py:42: Forbidden variable name 'data' found. Use a more descriptive name or add '# maintainability: ignore[meaningless-variable-name]' to suppress. See https://hilton.org.uk/blog/meaningless-variable-names
```

**If no violations:**

```
forbid meaningless variable names...............................Passed
```

### Running Manually

Run the hook on all files:

```bash
pre-commit run forbid-vars --all-files
```

Run on specific files:

```bash
pre-commit run forbid-vars --files src/main.py src/utils.py
```

Run all configured hooks:

```bash
pre-commit run --all-files
```

## Configuration

### Custom Forbidden Names

By default, the hook forbids `data` and `result`. To customize:

```yaml
repos:
  - repo: https://github.com/<user>/pre-commit-extra-hooks
    rev: v1.0.0
    hooks:
      - id: forbid-vars
        args: ["--names=data,result,info,temp,obj,value"]
```

### Inline Suppression

Suppress violations on specific lines using an inline comment:

```python
# This will trigger a violation:
data = load_from_database()

# This will be ignored:
data = load_from_database()  # maintainability: ignore[meaningless-variable-name]
```

**Important:** The ignore comment must be on the same line as the violation.

## Examples

### Example 1: Default Configuration

**`.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/<user>/pre-commit-extra-hooks
    rev: v1.0.0
    hooks:
      - id: forbid-vars
```

**Code that passes:**

```python
def calculate_total(invoice_items):
    """Calculate total from invoice items"""
    total_amount = 0
    for item in invoice_items:
        total_amount += item.price * item.quantity
    return total_amount
```

**Code that fails:**

```python
def process():
    """Process data"""
    data = fetch()  # ❌ Violation: 'data' is forbidden
    result = transform(data)  # ❌ Violation: 'result' is forbidden
    return result
```

**Error output:**

```
src/process.py:3: Forbidden variable name 'data' found. Use a more descriptive name or add '# maintainability: ignore[meaningless-variable-name]' to suppress. See https://hilton.org.uk/blog/meaningless-variable-names
src/process.py:4: Forbidden variable name 'result' found. Use a more descriptive name or add '# maintainability: ignore[meaningless-variable-name]' to suppress. See https://hilton.org.uk/blog/meaningless-variable-names
```

### Example 2: Custom Forbidden Names

**`.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/<user>/pre-commit-extra-hooks
    rev: v1.0.0
    hooks:
      - id: forbid-vars
        args: ["--names=data,result,info,temp,obj,value"]
```

**Code that now also fails:**

```python
def get_user():
    temp = fetch_user()  # ❌ Violation: 'temp' now forbidden
    info = temp.get_details()  # ❌ Violation: 'info' now forbidden
    return info
```

### Example 3: Using Inline Suppression

**Code with suppressions:**

```python
def legacy_code():
    """Legacy code with necessary suppressions"""
    # New code - should use descriptive names
    user_records = fetch_users()

    # Legacy code - suppressed because refactoring is risky
    data = transform(user_records)  # maintainability: ignore[meaningless-variable-name]
    result = validate(data)  # maintainability: ignore[meaningless-variable-name]

    return result
```

**Result:** Hook passes (violations suppressed on lines 7 and 8).

### Example 4: Function Parameters

**Code that fails:**

```python
def process(data):  # ❌ Violation: parameter 'data'
    """Process data"""
    return transform(data)

def transform(*, result=None):  # ❌ Violation: parameter 'result'
    """Transform result"""
    return result
```

**Fixed version:**

```python
def process(user_records):  # ✅ Descriptive parameter name
    """Process user records"""
    return transform(user_records)

def transform(*, transformed_output=None):  # ✅ Descriptive parameter name
    """Transform output"""
    return transformed_output
```

## Troubleshooting

### Hook not running

**Problem:** Hook doesn't run on commit.

**Solution:** Make sure you've installed the git hooks:

```bash
pre-commit install
```

### Hook runs but no violations reported despite bad code

**Problem:** Code with `data` variable passes the hook.

**Solution:** Check if:

1. File is a Python file (hook only runs on `*.py` files)
2. Inline ignore comment is present
3. The variable is actually being assigned (not an attribute like `obj.data`)

### Syntax error in code

**Problem:** Hook exits with error on syntactically invalid Python.

**Solution:** The hook requires valid Python syntax to parse the AST. Fix syntax errors first:

```bash
# Check syntax
python -m py_compile src/file.py
```

### Too many false positives

**Problem:** Hook catches too many legitimate uses.

**Solution:** Use inline suppression for legitimate cases:

```python
# Legitimate use in test fixtures
def test_parser():
    data = "test input"  # maintainability: ignore[meaningless-variable-name]
    assert parse(data) == expected
```

Or customize the blacklist to be more specific to your project.

## Advanced Usage

### Running Hooks in CI/CD

Add to your CI pipeline (GitHub Actions example):

```yaml
name: Pre-commit Checks
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install pre-commit
        run: pip install pre-commit
      - name: Run pre-commit hooks
        run: pre-commit run --all-files
```

### Auto-updating Hooks

Keep hooks up to date:

```bash
# Update to latest versions
pre-commit autoupdate

# See what would be updated
pre-commit autoupdate --dry-run
```

### Temporarily Skipping Hooks

Skip hooks for a single commit (use sparingly):

```bash
git commit -m "Emergency fix" --no-verify
```

### Running Multiple Hooks

Combine with other pre-commit hooks:

```yaml
repos:
  - repo: https://github.com/<user>/pre-commit-extra-hooks
    rev: v1.0.0
    hooks:
      - id: forbid-vars

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## Best Practices

### 1. Start with defaults, customize if needed

The default blacklist (`data`, `result`) catches the most common offenders. Only add more if you find project-specific patterns.

### 2. Use inline suppression sparingly

Every suppression is a code smell. Before adding `# maintainability: ignore`:

- Ask: Can I use a more descriptive name?
- Document why the suppression is necessary
- Consider refactoring if suppressions accumulate

### 3. Run hooks before committing

Get immediate feedback:

```bash
# Stage changes
git add .

# Run hooks manually to check
pre-commit run

# If all pass, commit
git commit -m "Your message"
```

### 4. Keep hooks updated

Review and update hook versions quarterly:

```bash
pre-commit autoupdate
```

### 5. Educate your team

Share the reasoning behind forbidden names:

- Link: https://hilton.org.uk/blog/meaningless-variable-names
- Discuss in code reviews
- Add to project documentation

## Next Steps

- **Read the research**: See [research.md](./research.md) for implementation details
- **Review data model**: See [data-model.md](./data-model.md) for internal structure
- **Check contracts**: See [contracts/](./contracts/) for API specifications
- **Run implementation**: Use `/speckit.tasks` to generate implementation tasks

## Getting Help

- **Issues**: Report problems at https://github.com/<user>/pre-commit-extra-hooks/issues
- **Documentation**: See README.md in the repository
- **Pre-commit docs**: https://pre-commit.com/

## Summary

**Quick setup:**

1. Add to `.pre-commit-config.yaml`
2. Run `pre-commit install`
3. Commit as usual

**Key features:**

- Forbids `data` and `result` by default
- Customizable via `--names` argument
- Inline suppression with `# maintainability: ignore[meaningless-variable-name]`
- Works automatically on commit

**Remember:** The goal is better code clarity through descriptive variable names!
