# Research: Style and Maintainability Pre-commit Hooks

**Feature**: 002-style-maintainability-hooks
**Date**: 2025-11-30
**Purpose**: Research best practices and implementation strategies for three Python code quality hooks

## Research Questions

### 1. How to reliably detect and fix misplaced comments in Python source code?

**Decision**: Use Python's `tokenize` module to preserve comments while analyzing code structure

**Rationale**:

- Python's AST module strips comments during parsing, so we need tokenize to access comment tokens
- The tokenize module provides line-by-line tokens including COMMENT, NL (newline), NEWLINE, INDENT, DEDENT
- We can identify closing brackets (OP tokens with values ')', ']', '}') and check if a COMMENT token follows on the same line
- To move comments, we reconstruct the file by modifying the token stream and using `tokenize.untokenize()`
- This preserves all other formatting, indentation, and handles edge cases like comments in strings

**Alternatives Considered**:

- **Regex-based approach**: Rejected - Cannot reliably handle nested brackets, multi-line expressions, or comments within string literals
- **Line-by-line text processing**: Rejected - Would lose semantic understanding of what's a closing bracket vs string content
- **AST + manual comment extraction**: Rejected - More complex than using tokenize, which is designed for this use case

**Best Practices**:

- Use `tokenize.open()` to handle file encoding automatically
- Preserve exact indentation and whitespace (tokenize maintains this)
- For line length determination (inline vs preceding comment), use simple string length check against 88 characters
- Handle edge case: multiple comments on same line (keep them together)

**Implementation Strategy**:

1. Tokenize the file using `tokenize.generate_tokens()`
2. Build a list of (token_type, token_string, start, end, line) tuples
3. Scan for OP tokens with ')' ']' '}' followed by COMMENT on same line
4. If closing bracket is on a line with no other code, mark comment for movement
5. Determine target line (the line with actual expression content)
6. Check if inline placement would exceed 88 chars; if so, use preceding comment
7. Reconstruct token stream with comment moved
8. Write back using `tokenize.untokenize()` or manual line reconstruction

### 2. How to detect and collapse excessive blank lines after module headers?

**Decision**: Use line-by-line text processing with module header detection logic

**Rationale**:

- This is primarily a whitespace issue, not a syntax issue, so tokenize/AST are overkill
- We need to detect "module-level comments/docstrings" which appear before first import/class/function
- Simple state machine: track if we've seen first code element, count consecutive blank lines, collapse when needed
- Must preserve copyright comment spacing (one blank line after copyright)

**Alternatives Considered**:

- **Tokenize module**: Rejected - Overkill for blank line counting; adds complexity without benefit
- **AST analysis**: Rejected - AST doesn't preserve blank line information
- **Regex replacement**: Rejected - Hard to distinguish module-level blanks from function-level blanks

**Best Practices**:

- Detect copyright comments with pattern: `# Copyright` or `# (c)` or `# ©`
- Consider shebang (#!) and encoding declarations (# -_- coding: utf-8 -_-) as module headers
- Module docstrings are triple-quoted strings appearing before any import/class/function/assignment
- After detecting end of module header area, collapse 2+ consecutive blank lines to 1
- Preserve blank lines elsewhere in file (not module-level)

**Implementation Strategy**:

1. Read file line by line
2. Track state: IN_MODULE_HEADER, AFTER_MODULE_HEADER, IN_CODE
3. Detect end of module header: first import, class, def, or assignment
4. In AFTER_MODULE_HEADER state, count consecutive blank lines
5. If count >= 2, collapse to 1 blank line
6. Special case: after copyright comment, preserve exactly 1 blank line
7. Write modified lines back to file

### 3. How to detect redundant super().**init**(\*\*kwargs) patterns?

**Decision**: Use Python AST to analyze class hierarchies and **init** signatures

**Rationale**:

- Requires understanding class inheritance and method signatures - AST is designed for this
- `ast.ClassDef` nodes contain bases (parent classes) and body (methods)
- Can traverse AST to find **init** methods that accept \*\*kwargs
- Need to inspect parent class **init** to determine if it accepts arguments
- Limited to same-file parent classes and standard library (cannot analyze arbitrary imports)

**Alternatives Considered**:

- **Runtime inspection with inspect module**: Rejected - Would require importing user code, which is unsafe and complex
- **Regex for super() calls**: Rejected - Cannot determine parent class signature from regex
- **Static analysis only**: Chosen - Safer, faster, and sufficient for most cases

**Best Practices**:

- Use `ast.parse()` to build AST from source file
- Use `ast.NodeVisitor` to traverse and find ClassDef nodes
- For each class with **init**, check if it has \*\*kwargs parameter
- If yes, find super().**init**() call and check if \*\*kwargs is forwarded
- Attempt to resolve parent class from bases (limited to same-file or stdlib)
- If parent **init** accepts no arguments, report violation
- If parent cannot be resolved, skip (too complex for static analysis)

**Implementation Strategy**:

1. Parse file with `ast.parse(source, filename)`
2. Create visitor class extending `ast.NodeVisitor`
3. Override `visit_ClassDef` to analyze each class
4. Within class, find FunctionDef named '**init**'
5. Check if args.kwarg is not None (has \*\*kwargs)
6. Find Call nodes where func is Attribute(value=Name('super'), attr='**init**')
7. Check if keywords contains \*\*kwargs (Starred node in keywords)
8. Attempt to resolve parent class:
   - If base is Name, look up in same file's class definitions
   - If base is Attribute and module is known stdlib, can skip (stdlib rarely has zero-arg **init**)
9. If parent **init** in same file and has no args beyond self, report violation
10. Produce error message with file:line:message format

### 4. Command-line interface design for pre-commit hooks

**Decision**: Use argparse with file paths as positional arguments, optional --fix flag

**Rationale**:

- Pre-commit framework passes file paths as positional arguments
- Standard pattern: hooks accept files, process them, return exit code
- --fix flag enables auto-fix mode (some hooks detection-only by default)
- Exit code 0 = no violations, 1 = violations found/fixed

**Best Practices**:

- Accept multiple file paths: `parser.add_argument('filenames', nargs='*')`
- Add --fix flag: `parser.add_argument('--fix', action='store_true')`
- Process each file independently; aggregate exit codes (if any file fails, return non-zero)
- Print violations to stderr: `print(f"{filename}:{line}: {message}", file=sys.stderr)`
- For auto-fix hooks, modify file in-place and return 1 to signal changes made
- Handle exceptions gracefully: catch syntax errors, continue to next file

**Implementation Pattern**:

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    parser.add_argument('--fix', action='store_true')
    args = parser.parse_args()

    exit_code = 0
    for filename in args.filenames:
        try:
            violations = check_file(filename)
            if violations:
                if args.fix:
                    fix_file(filename, violations)
                    print(f"Fixed: {filename}", file=sys.stderr)
                    exit_code = 1  # Signal changes made
                else:
                    for line, msg in violations:
                        print(f"{filename}:{line}: {msg}", file=sys.stderr)
                    exit_code = 1
        except SyntaxError:
            print(f"{filename}: Syntax error, skipping", file=sys.stderr)
            # Don't fail on syntax errors

    return exit_code
```

### 5. Testing strategy for pre-commit hooks

**Decision**: Use pytest with fixture files for good/bad examples

**Rationale**:

- pytest is the standard Python testing framework
- Fixture files allow testing realistic code examples
- Can test both detection and auto-fix modes
- Easy to validate error messages and exit codes

**Best Practices**:

- Create fixtures/ directory with subdirectories per hook
- Each subdirectory has good/ and bad/ subdirs with Python files
- Tests use `tmp_path` fixture to create temporary files
- Test exit codes: assert exit_code == 0 for good files, != 0 for bad files
- Test error messages: assert expected filename:line in stderr
- Test auto-fix: write bad file, run with --fix, read result, assert equals good file
- Test edge cases: empty files, syntax errors, complex nested structures

**Test Organization**:

```
tests/
├── fixtures/
│   ├── misplaced_comments/
│   │   ├── good/
│   │   │   └── inline_comment.py
│   │   └── bad/
│   │       └── trailing_on_bracket.py
│   ├── excessive_blank_lines/
│   └── redundant_super_init/
├── test_fix_misplaced_comments.py
├── test_fix_excessive_blank_lines.py
└── test_check_redundant_super_init.py
```

## Summary

All research questions resolved. Key technical decisions:

1. **STYLE-001 (Misplaced Comments)**: Use tokenize module to preserve comments, move them based on line length heuristic
2. **STYLE-002 (Excessive Blank Lines)**: Use simple line-by-line state machine to detect and collapse blank lines after module headers
3. **MAINTAINABILITY-006 (Redundant Super Init)**: Use AST visitor pattern to analyze class hierarchies and detect signature mismatches
4. **CLI Interface**: Standard argparse pattern with file paths and --fix flag
5. **Testing**: pytest with fixture files for realistic test cases

No blocking unknowns remain. Ready to proceed to Phase 1 (design artifacts).
