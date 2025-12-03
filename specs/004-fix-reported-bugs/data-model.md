# Data Model

## Overview

This feature involves bug fixes to existing pre-commit hooks and does not introduce new data models. The hooks operate on Python source files in-memory and modify them in-place. However, we can document the key entities that the hooks work with conceptually.

## Conceptual Entities

### 1. Linter Pragma Comment

**Description**: A special comment that provides directives to linting, type-checking, or analysis tools.

**Attributes**:
- `text` (string): The full comment text including the `#` character
- `line_number` (integer): The 1-based line number where the comment appears
- `pragma_type` (string): The type of pragma (e.g., "noqa", "type: ignore", "pragma")
- `tool` (string): The tool the pragma is intended for (e.g., "flake8", "mypy", "coverage")

**Behavior**:
- Must remain on the same line as the code it modifies
- Should not be moved by the `fix-misplaced-comments` hook
- Pattern-matched using regex against a blacklist

**Examples**:
```python
result = func()  # noqa: E501
value = cast(int, obj)  # type: ignore
if DEBUG:  # pragma: no cover
    log_debug()
```

---

### 2. Bracket-Only Line

**Description**: A line in Python source code that contains only closing bracket characters (`)`, `}`, `]`) and optional whitespace, possibly with a comment.

**Attributes**:
- `line_number` (integer): The 1-based line number
- `bracket_chars` (list of strings): The bracket characters on the line (e.g., `[")"]`, `[")", ")"]`)
- `has_comment` (boolean): Whether the line contains a comment
- `comment_text` (string, optional): The comment text if present
- `indentation` (integer): Number of leading whitespace characters

**Behavior**:
- Comments on bracket-only lines should be moved to the preceding code line
- Lines with both code AND brackets are NOT bracket-only lines
- Identified using tokenize module to check token types

**Examples**:
```python
# Bracket-only line (comment should be moved)
result = func(
    arg1,
    arg2,
)  # This comment is misplaced

# NOT a bracket-only line (comment stays)
result = func(arg1, arg2)  # This comment is fine
```

---

### 3. File Header Comment Block

**Description**: A contiguous block of comment lines at the beginning of a Python file, typically containing copyright notices, license information, or module-level documentation.

**Attributes**:
- `start_line` (integer): The 1-based line number where the header starts (usually 1)
- `end_line` (integer): The 1-based line number where the header ends
- `content_lines` (list of strings): The actual comment lines
- `includes_shebang` (boolean): Whether the header includes a shebang line
- `includes_encoding` (boolean): Whether the header includes an encoding declaration
- `includes_docstring` (boolean): Whether the header includes a module docstring

**Behavior**:
- Identified by `find_module_header_end()` function
- The region from `end_line` to the first non-blank code line is where blank line collapsing applies
- Header content itself is never modified

**Examples**:
```python
# Example 1: Copyright header
# Copyright 2025 Example Corp
# Licensed under MIT License

import os

# Example 2: With docstring
"""Module for user authentication.

This module provides...
"""

import os
```

---

### 4. Token

**Description**: A lexical token from Python source code, as produced by the `tokenize` module.

**Attributes** (from tokenize.TokenInfo):
- `type` (integer): Token type constant (e.g., `tokenize.OP`, `tokenize.COMMENT`)
- `string` (string): The actual text of the token
- `start` (tuple): (line_number, column) where the token starts
- `end` (tuple): (line_number, column) where the token ends
- `line` (string): The logical line containing the token

**Behavior**:
- Used to precisely identify brackets, comments, and code structure
- Enables accurate detection of bracket-only lines
- Already used by existing implementation

**Relevant Token Types for This Feature**:
- `tokenize.OP`: Operators including brackets `(`, `)`, `{`, `}`, `[`, `]`
- `tokenize.COMMENT`: Comment tokens starting with `#`
- `tokenize.NEWLINE`, `tokenize.NL`: Line terminators
- `tokenize.INDENT`, `tokenize.DEDENT`: Indentation changes

---

## State Transitions

### Fix Misplaced Comments Hook

```
Input File
    ↓
[Tokenize] → Token List
    ↓
[Scan for closing brackets]
    ↓
[Check for comment on same line] → No comment found → Skip
    ↓ Comment found
[Check if linter pragma] → Yes → Skip (don't move)
    ↓ Not a pragma
[Check if bracket-only line] → No (has code) → Skip (don't move)
    ↓ Yes (bracket-only)
[Move comment to previous line]
    ↓
[Write modified file]
```

### Fix Excessive Blank Lines Hook

```
Input File
    ↓
[Read lines]
    ↓
[Find header end] → find_module_header_end()
    ↓
[Find first code line after header]
    ↓
[Count blank lines in header→code region]
    ↓
[Collapse excessive blanks (2+ → 1)]
    ↓
[Preserve rest of file unchanged]
    ↓
[Write modified file]
```

---

## Implementation Notes

### No Persistent Storage

These hooks operate entirely in-memory:
1. Read source file
2. Analyze and transform in memory
3. Write back to same file

### No External Dependencies

All data structures use Python standard library:
- `tokenize.TokenInfo` for token representation
- `list[str]` for line-based operations
- `re.Pattern` for pragma matching

### Error Handling

- Invalid Python syntax: Skip file (return empty violations list)
- Unicode decode errors: Skip file
- File I/O errors: Skip file (fail gracefully)
