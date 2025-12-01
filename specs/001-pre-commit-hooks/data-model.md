# Data Model: Forbid Variable Names Hook

## Overview

The forbid-vars hook operates on Python source code files, analyzing their Abstract Syntax Trees (AST) to detect forbidden variable names. The data model is minimal since this is a stateless validation tool with no persistent storage.

## Entities

### 1. Violation

Represents a single instance of a forbidden variable name found in source code.

**Fields:**

- `name` (string): The forbidden variable name that was detected (e.g., "data", "result")
- `line` (integer): Line number in the source file where the violation occurred
- `filepath` (string): Path to the file containing the violation (used for reporting)

**Lifecycle:**

- Created when AST visitor detects a forbidden name
- Filtered against ignored lines
- Reported to user via stderr
- Discarded after reporting (no persistence)

**Validation Rules:**

- `name` must be non-empty string
- `line` must be positive integer (1-indexed)
- `filepath` must be valid file path

**Example:**

```python
{
    'name': 'data',
    'line': 42,
    'filepath': 'src/process.py'
}
```

### 2. ForbiddenNameSet

Represents the configured set of variable names that are not allowed.

**Fields:**

- `names` (set of strings): Forbidden variable names to check for

**Source:**

- Default: `{'data', 'result'}` (per user requirement)
- Override: Parsed from `--names` CLI argument (comma-separated list)

**Validation Rules:**

- Must contain at least one name
- Names must be valid Python identifiers
- Names are case-sensitive (Python convention)

**Example:**

```python
# Default
{'data', 'result'}

# Custom via --names argument
{'data', 'result', 'info', 'temp', 'obj', 'value'}
```

### 3. IgnoreDirective

Represents a line in the source code with an inline ignore comment.

**Fields:**

- `line` (integer): Line number where the ignore comment appears

**Source:**

- Parsed from Python file comments using `tokenize` module
- Pattern: `# maintainability: ignore[meaningless-variable-name]` (case-insensitive)

**Lifecycle:**

- Extracted during file processing
- Stored in set of line numbers
- Used to filter violations before reporting
- Discarded after file processing completes

**Example:**

```python
# Set of ignored line numbers
{15, 23, 42}

# Source code example:
data = load()  # maintainability: ignore[meaningless-variable-name]  <- line 42
```

## Relationships

```
ForbiddenNameSet ──────> AST Visitor ──────> Violation (many)
                              │
                              │
IgnoreDirective Set <─────────┘
      │
      │ (filters)
      ▼
Final Violations (reported to user)
```

**Flow:**

1. `ForbiddenNameSet` is configured from defaults or CLI args
2. `IgnoreDirective` set is extracted from file comments
3. AST Visitor processes file, creating `Violation` instances
4. Violations on ignored lines are filtered out
5. Remaining violations are reported

## State Transitions

### File Processing State Machine

```
START
  │
  ├─> Parse file with ast.parse()
  │   ├─> Success: Continue
  │   └─> Syntax Error: Skip file (AST requires valid Python)
  │
  ├─> Extract ignore directives (tokenize)
  │   └─> Build set of ignored line numbers
  │
  ├─> Run AST visitor
  │   └─> Collect all violations
  │
  ├─> Filter violations
  │   └─> Remove violations on ignored lines
  │
  ├─> Report violations
  │   ├─> No violations: Exit 0 (success)
  │   └─> Has violations: Report + Exit 1 (failure)
  │
END
```

### Violation Detection States

```
AST Node Visited
  │
  ├─> Is it a variable definition context?
  │   (Assign, AnnAssign, FunctionDef, AsyncFunctionDef)
  │   │
  │   ├─> YES: Extract variable name
  │   │   │
  │   │   ├─> Is name in ForbiddenNameSet?
  │   │   │   │
  │   │   │   ├─> YES: Create Violation
  │   │   │   │
  │   │   │   └─> NO: Continue
  │   │   │
  │   │   └─> Continue visiting child nodes
  │   │
  │   └─> NO: Continue visiting child nodes
  │
END
```

## Data Structures (Python Implementation)

### Core Data Structures

```python
from typing import TypedDict, Set

class Violation(TypedDict):
    """Represents a forbidden variable name violation"""
    name: str      # The forbidden name found
    line: int      # Line number where it appears

# Note: filepath is passed separately to reporting function

ForbiddenNameSet = Set[str]
"""Set of variable names that are forbidden"""

IgnoredLines = Set[int]
"""Set of line numbers with ignore comments"""
```

### AST Visitor Structure

```python
import ast

class ForbiddenNameVisitor(ast.NodeVisitor):
    """
    AST visitor that detects forbidden variable names.

    Attributes:
        forbidden_names: Set of names to check for
        violations: List of detected violations
    """
    def __init__(self, forbidden_names: Set[str]) -> None:
        self.forbidden_names = forbidden_names
        self.violations: list[Violation] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        """Process regular assignments: data = 1"""
        ...

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Process annotated assignments: data: int = 1"""
        ...

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Process function definitions: def foo(data):"""
        ...

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Process async function definitions: async def foo(data):"""
        ...

    def _check_name(self, name: str, lineno: int) -> None:
        """Check if name is forbidden and record violation"""
        ...
```

## Constraints

### Performance Constraints

- **File Processing**: O(n) where n = number of AST nodes in file
- **Violation Detection**: O(1) name lookup in set
- **Memory**: Violations list size bounded by file size
- **Target**: <5 seconds for repos with <1000 files (SC-002)

### Data Constraints

- **Variable Names**: Must be valid Python identifiers
- **Line Numbers**: Must be positive integers (1-indexed, from AST)
- **File Paths**: Must be accessible and readable by the process
- **Python Files**: Must be syntactically valid for AST parsing

### Operational Constraints

- **No Persistent Storage**: All data structures are ephemeral
- **No External Dependencies**: Uses only Python stdlib (ast, tokenize, re)
- **Stateless**: Each file processed independently
- **Thread-Safe**: No shared state between file processing

## Edge Cases

### Empty/Invalid Input

```python
# Empty file
# Result: No violations (success)

# Syntactically invalid Python
# Result: Skip file (cannot parse AST)
def foo(
# Missing closing paren - AST parse will fail
```

### Attribute Access vs Variable

```python
# These are NOT violations (obj.data is an attribute, not a variable)
obj.data = 5
self.result = compute()
config.data.fetch()

# This IS a violation (data is a variable)
data = obj.fetch()
```

### Ignore Comment Variations

```python
# All of these should work (case-insensitive):
data = 1  # maintainability: ignore[meaningless-variable-name]
data = 2  # MAINTAINABILITY: IGNORE[MEANINGLESS-VARIABLE-NAME]
data = 3  #maintainability:ignore[meaningless-variable-name]

# This should NOT work (wrong pattern):
data = 4  # noqa: ignore meaningless variable
```

### Multiple Variables on One Line

```python
# Multiple assignment targets
data, result = get_values()
# Result: 2 violations (both 'data' and 'result'), same line number

# With ignore comment
data, result = get_values()  # maintainability: ignore[meaningless-variable-name]
# Result: Both violations suppressed
```

### Function Parameters

```python
# All of these should be detected:
def foo(data):           # Violation on this line
    pass

def bar(x, *, data=None):  # Violation on this line
    pass

def baz(*data):          # Violation on this line
    pass

def qux(**data):         # Violation on this line
    pass

async def process(data):  # Violation on this line
    pass
```

## Summary

The data model for the forbid-vars hook is intentionally minimal and stateless:

- **3 core entities**: Violation, ForbiddenNameSet, IgnoreDirective
- **No persistence**: All data structures are ephemeral
- **Efficient processing**: O(n) complexity with set-based lookups
- **Clear relationships**: Configuration → Detection → Filtering → Reporting
- **Edge case handling**: Documented behavior for all known scenarios

This simplicity aligns with Constitutional Principle V (Simplicity and Maintainability) and ensures the hook remains fast, maintainable, and easy to understand.
