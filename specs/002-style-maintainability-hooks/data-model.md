# Data Model: Style and Maintainability Pre-commit Hooks

**Feature**: 002-style-maintainability-hooks
**Date**: 2025-11-30
**Purpose**: Define internal data structures for hook implementations

## Overview

These hooks process Python source files and produce violation reports or fixed files. The data model focuses on representing violations, file context, and transformation operations.

## Core Entities

### Violation

Represents a single detected code quality issue.

**Attributes**:

- `filename: str` - Path to the file containing the violation
- `line_number: int` - Line number where violation occurs (1-indexed)
- `column: int | None` - Column number if applicable
- `violation_type: str` - Type identifier (e.g., "STYLE-001", "STYLE-002", "MAINTAINABILITY-006")
- `message: str` - Human-readable description of the violation
- `suggestion: str | None` - Optional suggestion for how to fix

**Validation Rules**:

- `line_number` must be positive integer
- `filename` must be valid path
- `message` must be non-empty and actionable

**Example**:

```python
Violation(
    filename="src/example.py",
    line_number=15,
    column=None,
    violation_type="STYLE-001",
    message="Comment on closing bracket line should be moved to expression line",
    suggestion="Move comment to line 14 or make it a preceding comment on line 13"
)
```

### FileContext (STYLE-001: Misplaced Comments)

Represents the parsed structure of a Python file for comment analysis.

**Attributes**:

- `filename: str` - Path to the file
- `encoding: str` - File encoding (e.g., "utf-8")
- `tokens: list[TokenInfo]` - List of tokens from tokenize module
- `lines: list[str]` - Original source lines

**TokenInfo** (from Python stdlib):

- `type: int` - Token type (COMMENT, OP, NL, NEWLINE, etc.)
- `string: str` - Token content
- `start: tuple[int, int]` - (line, column) start position
- `end: tuple[int, int]` - (line, column) end position
- `line: str` - Full line content

**Operations**:

- `find_misplaced_comments() -> list[MisplacedComment]` - Identify comments on closing bracket lines
- `fix_comment_placement(comment: MisplacedComment) -> list[TokenInfo]` - Generate fixed token stream

### MisplacedComment (STYLE-001 internal)

Represents a comment that needs to be moved.

**Attributes**:

- `comment_token: TokenInfo` - The COMMENT token
- `closing_bracket_token: TokenInfo` - The closing bracket token before the comment
- `target_line: int` - Line number where comment should move to
- `placement_style: str` - "inline" or "preceding"

**Derived Values**:

- `placement_style` determined by: if target line + comment length <= 88 chars, use "inline", else "preceding"

### FileLines (STYLE-002: Excessive Blank Lines)

Represents file structure for blank line analysis.

**Attributes**:

- `filename: str` - Path to the file
- `lines: list[str]` - All lines in the file
- `module_header_end: int | None` - Line number where module header ends (0-indexed)
- `encoding: str` - File encoding

**State Tracking**:

- `has_copyright: bool` - Whether file contains copyright notice
- `has_module_docstring: bool` - Whether file has module-level docstring
- `first_code_line: int | None` - First non-header, non-blank line

**Operations**:

- `find_excessive_blank_lines() -> list[BlankLineRun]` - Find runs of 2+ blank lines after module header
- `collapse_blank_lines(run: BlankLineRun) -> list[str]` - Collapse blank lines to single line

### BlankLineRun (STYLE-002 internal)

Represents consecutive blank lines to be collapsed.

**Attributes**:

- `start_line: int` - First blank line (0-indexed)
- `end_line: int` - Last blank line (0-indexed)
- `count: int` - Number of blank lines (end_line - start_line + 1)
- `after_copyright: bool` - Whether this run immediately follows copyright comment

**Validation**:

- `count >= 2` (only track runs of 2+ blank lines)
- If `after_copyright` is True, preserve exactly 1 blank line instead of collapsing all

### ClassContext (MAINTAINABILITY-006: Redundant Super Init)

Represents a Python class for inheritance analysis.

**Attributes**:

- `name: str` - Class name
- `line_number: int` - Line where class is defined
- `bases: list[str]` - Parent class names
- `init_method: InitMethod | None` - The **init** method if present

**Operations**:

- `has_init() -> bool` - Whether class defines **init**
- `resolve_parent_init(class_name: str) -> InitSignature | None` - Resolve parent **init** signature

### InitMethod (MAINTAINABILITY-006 internal)

Represents a class **init** method.

**Attributes**:

- `line_number: int` - Line where **init** is defined
- `has_kwargs: bool` - Whether signature includes \*\*kwargs
- `super_calls: list[SuperCall]` - List of super().**init**() calls

**Derived Values**:

- `forwards_kwargs: bool` - True if any super_call forwards \*\*kwargs

### SuperCall (MAINTAINABILITY-006 internal)

Represents a super().**init**(...) call.

**Attributes**:

- `line_number: int` - Line where call occurs
- `forwards_kwargs: bool` - Whether \*\*kwargs is passed to super().**init**()

### InitSignature (MAINTAINABILITY-006 internal)

Represents the signature of a parent **init** method.

**Attributes**:

- `class_name: str` - Parent class name
- `accepts_args: bool` - Whether **init** accepts any arguments beyond self
- `has_kwargs: bool` - Whether **init** accepts \*\*kwargs

**Validation Logic**:

- If child `forwards_kwargs` is True and parent `accepts_args` is False, report violation

## Relationships

```
Violation
  ├── Used by all three hooks to report issues
  └── Aggregated into exit code (any violations → exit 1)

STYLE-001 Flow:
  FileContext → find_misplaced_comments() → MisplacedComment[] → fix_comment_placement() → Updated FileContext

STYLE-002 Flow:
  FileLines → find_excessive_blank_lines() → BlankLineRun[] → collapse_blank_lines() → Updated FileLines

MAINTAINABILITY-006 Flow:
  AST → ClassContext[] → InitMethod → SuperCall + resolve_parent_init() → Violation[]
```

## File Encoding and Line Endings

All hooks must preserve:

- **Encoding**: Use `tokenize.open()` or detect with `tokenize.detect_encoding()`
- **Line Endings**: Detect from file (CRLF on Windows, LF on Unix) and preserve when writing

**Implementation**:

```python
import tokenize

# Reading with encoding preservation
with tokenize.open(filename) as f:
    content = f.read()

# Detect line ending
line_ending = '\r\n' if '\r\n' in content else '\n'

# Writing with preserved encoding and line endings
with open(filename, 'w', encoding=encoding, newline='') as f:
    f.write(line_ending.join(lines))
```

## State Transitions

### STYLE-001 (Comment Placement)

```
File → Tokenize → Identify Misplaced Comments → Determine Target Line → Fix → Write
```

States:

1. **Scanning**: Reading tokens, looking for closing brackets followed by comments
2. **Analyzing**: For each candidate, determine if comment is misplaced
3. **Fixing**: Move comment to target line (inline or preceding)
4. **Writing**: Reconstruct file from modified token stream

### STYLE-002 (Blank Lines)

```
File → Read Lines → Detect Module Header End → Find Blank Runs → Collapse → Write
```

States:

1. **Header Detection**: Scanning for end of module-level content
2. **Blank Line Counting**: After header, count consecutive blank lines
3. **Collapsing**: Replace 2+ blank lines with 1
4. **Writing**: Write modified lines back

### MAINTAINABILITY-006 (Super Init)

```
File → Parse AST → Find Classes → Analyze __init__ → Check Parent → Report
```

States:

1. **Parsing**: Build AST from source
2. **Traversal**: Visit ClassDef nodes
3. **Init Analysis**: Check for **init** with \*\*kwargs forwarding
4. **Parent Lookup**: Attempt to resolve parent **init** signature
5. **Validation**: If parent accepts no args but child forwards kwargs, report violation

## Summary

The data model focuses on:

- **Violations** as the common output format across all hooks
- **FileContext/FileLines/ClassContext** as input representations
- **Internal entities** (MisplacedComment, BlankLineRun, InitMethod) for transformation logic
- **Encoding and line ending preservation** to avoid breaking user files
- **State machines** for each hook's processing flow

All entities are simple, focused data structures using Python stdlib types. No external dependencies required.
