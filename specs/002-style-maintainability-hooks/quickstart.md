# Quickstart Guide: Style and Maintainability Hooks

**Feature**: 002-style-maintainability-hooks
**Audience**: Developers implementing these hooks
**Purpose**: Provide step-by-step implementation guidance

## Overview

This guide walks through implementing three Python pre-commit hooks:
1. **fix-misplaced-comments** (STYLE-001): Auto-fix trailing comments on closing brackets
2. **fix-excessive-blank-lines** (STYLE-002): Auto-fix excessive blank lines after module headers
3. **check-redundant-super-init** (MAINTAINABILITY-006): Detect redundant **kwargs forwarding

## Prerequisites

- Python 3.8+ installed
- Existing pre_commit_extra_hooks repository with infrastructure from feature 001
- pytest installed for testing
- ruff configured for linting

## Implementation Roadmap

### Phase 1: Project Structure Setup

Create the necessary directories and skeleton files:

```bash
# From repository root
mkdir -p src/pre_commit_hooks
mkdir -p tests/fixtures/{misplaced_comments,excessive_blank_lines,redundant_super_init}/{good,bad}

touch src/pre_commit_hooks/__init__.py
touch src/pre_commit_hooks/fix_misplaced_comments.py
touch src/pre_commit_hooks/fix_excessive_blank_lines.py
touch src/pre_commit_hooks/check_redundant_super_init.py

touch tests/test_fix_misplaced_comments.py
touch tests/test_fix_excessive_blank_lines.py
touch tests/test_check_redundant_super_init.py
```

### Phase 2: Implement STYLE-001 (Misplaced Comments)

**File**: `src/pre_commit_hooks/fix_misplaced_comments.py`

**Key Components**:

1. **Import required modules**:
   ```python
   import argparse
   import sys
   import tokenize
   from pathlib import Path
   ```

2. **Main detection logic**:
   - Use `tokenize.generate_tokens()` to parse file
   - Build token list
   - Scan for OP tokens with ')' ']' '}' followed by COMMENT on same line
   - Check if closing bracket is on a line with no other code

3. **Fix logic**:
   - Determine target line (line with expression content)
   - Calculate if inline comment would fit in 88 chars
   - Reconstruct token stream with comment moved
   - Write back to file with preserved encoding

4. **CLI interface**:
   ```python
   def main():
       parser = argparse.ArgumentParser()
       parser.add_argument('filenames', nargs='*')
       parser.add_argument('--fix', action='store_true')
       args = parser.parse_args()

       exit_code = 0
       for filename in args.filenames:
           violations = check_file(filename)
           if violations:
               if args.fix:
                   fix_file(filename)
                   print(f"Fixed: {filename}", file=sys.stderr)
               else:
                   for line, msg in violations:
                       print(f"{filename}:{line}: STYLE-001: {msg}", file=sys.stderr)
               exit_code = 1
       return exit_code
   ```

**Test Cases** (`tests/test_fix_misplaced_comments.py`):

```python
import pytest
from pre_commit_hooks.fix_misplaced_comments import main

def test_detects_trailing_comment_on_closing_paren(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(
        'result = func(\n'
        '    arg\n'
        ')  # Comment here\n'
    )

    # Run without --fix
    exit_code = main([str(test_file)])
    assert exit_code == 1  # Violation found

def test_fixes_misplaced_comment(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(
        'result = func(\n'
        '    arg\n'
        ')  # Comment\n'
    )

    # Run with --fix
    exit_code = main(['--fix', str(test_file)])
    assert exit_code == 1  # Changes made

    # Verify fix
    fixed = test_file.read_text()
    assert 'arg  # Comment' in fixed or '# Comment\n    arg' in fixed

def test_no_violation_for_correct_code(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(
        'result = func(\n'
        '    arg  # Comment inline\n'
        ')\n'
    )

    exit_code = main([str(test_file)])
    assert exit_code == 0  # No violations
```

### Phase 3: Implement STYLE-002 (Excessive Blank Lines)

**File**: `src/pre_commit_hooks/fix_excessive_blank_lines.py`

**Key Components**:

1. **Module header detection**:
   ```python
   def find_module_header_end(lines):
       """Find line number where module header ends."""
       in_module_docstring = False
       for i, line in enumerate(lines):
           stripped = line.strip()

           # Skip shebang, encoding, comments
           if stripped.startswith('#') or not stripped:
               continue

           # Module docstring
           if stripped.startswith('"""') or stripped.startswith("'''"):
               if not in_module_docstring:
                   in_module_docstring = True
               else:
                   return i + 1

           # First code line
           if stripped and not stripped.startswith('#'):
               return i

       return len(lines)
   ```

2. **Blank line detection and fixing**:
   ```python
   def fix_blank_lines(lines, header_end):
       """Collapse 2+ consecutive blank lines after header to 1."""
       fixed = lines[:header_end].copy()
       blank_count = 0

       for i in range(header_end, len(lines)):
           if lines[i].strip() == '':
               blank_count += 1
           else:
               if blank_count >= 2:
                   fixed.append('')  # Keep 1 blank line
               elif blank_count == 1:
                   fixed.append('')
               fixed.append(lines[i])
               blank_count = 0

       return fixed
   ```

**Test Cases**:

```python
def test_detects_excessive_blank_lines(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(
        '"""Module docstring."""\n'
        '\n'
        '\n'  # Extra blank line
        '\n'  # Another extra blank line
        'import something\n'
    )

    exit_code = main([str(test_file)])
    assert exit_code == 1

def test_preserves_copyright_spacing(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(
        '# Copyright (c) 2025\n'
        '\n'
        'import something\n'
    )

    exit_code = main(['--fix', str(test_file)])
    assert exit_code == 0  # Correct spacing preserved
```

### Phase 4: Implement MAINTAINABILITY-006 (Redundant Super Init)

**File**: `src/pre_commit_hooks/check_redundant_super_init.py`

**Key Components**:

1. **AST visitor**:
   ```python
   import ast

   class SuperInitChecker(ast.NodeVisitor):
       def __init__(self):
           self.violations = []
           self.classes = {}  # Track class definitions

       def visit_ClassDef(self, node):
           # Store class info
           self.classes[node.name] = node

           # Find __init__ method
           init_method = None
           for item in node.body:
               if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                   init_method = item
                   break

           if init_method:
               self.check_init_method(node, init_method)

           self.generic_visit(node)

       def check_init_method(self, class_node, init_node):
           # Check if __init__ has **kwargs
           has_kwargs = init_node.args.kwarg is not None

           if not has_kwargs:
               return

           # Find super().__init__() calls
           for stmt in ast.walk(init_node):
               if isinstance(stmt, ast.Call):
                   if self.is_super_init_call(stmt):
                       if self.forwards_kwargs(stmt):
                           # Check parent signature
                           for base in class_node.bases:
                               if isinstance(base, ast.Name):
                                   parent = self.classes.get(base.id)
                                   if parent:
                                       if not self.parent_accepts_args(parent):
                                           self.violations.append((
                                               init_node.lineno,
                                               f"Redundant **kwargs forwarded to {base.id}.__init__() which accepts no arguments"
                                           ))
   ```

**Test Cases**:

```python
def test_detects_redundant_kwargs_forwarding(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(
        'class Base:\n'
        '    def __init__(self):\n'
        '        pass\n'
        '\n'
        'class Child(Base):\n'
        '    def __init__(self, **kwargs):\n'
        '        super().__init__(**kwargs)\n'
    )

    exit_code = main([str(test_file)])
    assert exit_code == 1

def test_no_violation_when_parent_accepts_kwargs(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(
        'class Base:\n'
        '    def __init__(self, **kwargs):\n'
        '        pass\n'
        '\n'
        'class Child(Base):\n'
        '    def __init__(self, **kwargs):\n'
        '        super().__init__(**kwargs)\n'
    )

    exit_code = main([str(test_file)])
    assert exit_code == 0
```

### Phase 5: Update .pre-commit-hooks.yaml

Add the three new hooks to the repository's hook registry:

```yaml
# Append to existing .pre-commit-hooks.yaml
- id: fix-misplaced-comments
  name: Fix misplaced comments
  description: Move trailing comments on closing brackets to expression lines
  entry: python -m pre_commit_hooks.fix_misplaced_comments
  language: python
  types: [python]
  args: [--fix]

- id: fix-excessive-blank-lines
  name: Fix excessive blank lines
  description: Collapse multiple blank lines after module headers to one
  entry: python -m pre_commit_hooks.fix_excessive_blank_lines
  language: python
  types: [python]
  args: [--fix]

- id: check-redundant-super-init
  name: Check redundant super init kwargs
  description: Detect redundant **kwargs forwarding to parent __init__()
  entry: python -m pre_commit_hooks.check_redundant_super_init
  language: python
  types: [python]
```

### Phase 6: Update README.md

Document the new hooks in the repository README:

```markdown
## Available Hooks

### fix-misplaced-comments

Automatically fixes trailing comments that appear on closing bracket lines.

**Problem**: When auto-formatters move closing brackets to new lines, inline comments
become orphaned on bracket-only lines, losing context.

**Solution**: Moves comments to the expression line (inline if it fits, otherwise
as a preceding comment).

### fix-excessive-blank-lines

Collapses multiple consecutive blank lines after module headers to a single blank line.

**Problem**: Inconsistent spacing after module docstrings and top-level comments
creates visual clutter.

**Solution**: Enforces exactly one blank line between module headers and code.

### check-redundant-super-init

Detects when a class forwards `**kwargs` to a parent `__init__` that accepts no arguments.

**Problem**: Forwarding kwargs to parents that don't accept them creates misleading
inheritance patterns.

**Solution**: Reports violations with suggestions to remove unnecessary **kwargs.
```

### Phase 7: Testing and Validation

Run comprehensive tests:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src/pre_commit_hooks --cov-report=term-missing

# Run linting
ruff check src/ tests/

# Test hooks locally
python -m pre_commit_hooks.fix_misplaced_comments --fix src/**/*.py
python -m pre_commit_hooks.fix_excessive_blank_lines --fix src/**/*.py
python -m pre_commit_hooks.check_redundant_super_init src/**/*.py
```

## Implementation Checklist

- [ ] Create project structure (directories, skeleton files)
- [ ] Implement fix_misplaced_comments.py with tokenize-based analysis
- [ ] Write tests for fix_misplaced_comments (success, failure, edge cases)
- [ ] Implement fix_excessive_blank_lines.py with line-by-line processing
- [ ] Write tests for fix_excessive_blank_lines (including copyright spacing)
- [ ] Implement check_redundant_super_init.py with AST visitor
- [ ] Write tests for check_redundant_super_init (parent resolution)
- [ ] Update .pre-commit-hooks.yaml with three new hook entries
- [ ] Update README.md with hook descriptions and usage examples
- [ ] Run pytest with coverage (aim for >90% coverage)
- [ ] Run ruff linting (ensure all code passes)
- [ ] Test hooks on real Python codebases
- [ ] Document any edge cases or limitations found during testing

## Performance Targets

- Process 10,000 lines of code in under 5 seconds (all three hooks combined)
- Individual file processing: <1 second per 1000 lines
- Minimal memory usage: <100MB for typical files

## Next Steps

After implementation:

1. Run hooks on this repository itself (dogfooding)
2. Create example fixtures demonstrating each violation
3. Add integration tests with pre-commit framework
4. Tag release with version bump
5. Update documentation with real-world examples
