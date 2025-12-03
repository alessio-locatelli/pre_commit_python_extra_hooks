# Research for Bug Fixes

This document outlines the research findings for addressing the three bugs in the pre-commit hooks library.

## Phase 0: Research

### 1. BUG 1: `fix-misplaced-comments` - Ignore Comments

**Problem**: The hook currently moves ALL comments on closing bracket lines, including linter ignore directives (`# noqa`, `# type: ignore`, etc.), which breaks their functionality.

**Research Task**: Identify common linter ignore pragmas used in Python ecosystem and determine the best approach to preserve them.

**Sources Reviewed**:
- pylint documentation: `# pylint:` directives
- flake8 documentation: `# noqa` directives
- mypy documentation: `# type: ignore` directives
- ruff documentation: `# noqa`, `# type: ignore` support
- pyright documentation: `# pyright:` directives
- bandit documentation: `# nosec` directives
- coverage.py documentation: `# pragma: no cover` directives
- isort documentation: `# isort:` directives

**Decision**: Implement a blacklist of comment patterns that should NEVER be moved.

**Rationale**:
- Blacklist approach is simpler and more maintainable than trying to whitelist movable comments
- Linter pragmas are well-documented and follow consistent patterns
- Adding new patterns in the future is straightforward
- False negatives (not moving a comment that should be moved) are preferable to false positives (moving a pragma and breaking lint suppression)

**Alternatives Considered**:
- **Whitelist approach**: Only move comments that match certain patterns (e.g., regular explanatory comments). Rejected because it's more brittle and requires predicting all valid comment types.
- **AST analysis**: Use AST to determine if a comment is associated with a linter directive. Rejected because comments are not part of the AST in Python.
- **User configuration**: Allow users to specify which patterns to preserve. Rejected because it adds complexity for a problem that has a standard solution.

**Implementation Approach**:
```python
# Common linter ignore patterns (regex-friendly)
LINTER_PRAGMA_PATTERNS = [
    r'#\s*noqa',           # flake8, ruff
    r'#\s*type:\s*ignore', # mypy, pyright
    r'#\s*pragma:',        # coverage, general pragma
    r'#\s*pylint:',        # pylint
    r'#\s*pyright:',       # pyright
    r'#\s*mypy:',          # mypy
    r'#\s*flake8:',        # flake8
    r'#\s*ruff:',          # ruff
    r'#\s*bandit:',        # bandit
    r'#\s*nosec',          # bandit
    r'#\s*isort:',         # isort
]

# Check if comment contains any pragma pattern
def is_linter_pragma(comment_text: str) -> bool:
    return any(re.search(pattern, comment_text) for pattern in LINTER_PRAGMA_PATTERNS)
```

**Testing Strategy**: Create fixtures with various linter pragmas and verify they remain on their original lines.

---

### 2. BUG 2: `fix-misplaced-comments` - Bracket-Only Lines

**Problem**: The current logic in lines 68-71 checks if content before the bracket is empty OR ends with opening brackets. This condition is too broad and incorrectly identifies lines that have both code AND closing brackets as "bracket-only" lines.

**Current Logic Analysis** (lines 68-71):
```python
line_content = lines[token.start[0] - 1]
before_bracket = line_content[: token.start[1]].strip()

if not before_bracket or before_bracket.endswith(("(", "[", "{")):
    # Treats this as "bracket only line"
```

**Bug Example**:
```python
words = (words,) if isinstance(words, str) else words  # Comment
```
The bracket `)` appears at position after `else words`, so `before_bracket` = `"words = (words,) if isinstance(words, str) else words"`. This does NOT match the condition `not before_bracket or before_bracket.endswith(("(", "[", "{"))`, so theoretically this should work correctly.

**Re-analyzing Bug Report**: Looking at the bug report more carefully:
```diff
+    # All synonyms are stored here to prevent duplicates
     words = (words,) if isinstance(words, str) else words
-    synonyms: set[str] = set()  # All synonyms are stored here to prevent duplicates
```

This shows the comment was incorrectly moved FROM the `synonyms` line TO the `words` line. The issue is that the `set()` line ends with `)`, and the comment after it is being moved.

**Root Cause**: The current logic moves comments from ANY line with a closing bracket at the end, not just from lines that ONLY contain closing brackets. The check `before_bracket.endswith(("(", "[", "{"))` is meant to detect nested brackets but doesn't correctly identify bracket-only lines.

**Research Task**: Determine how to accurately identify lines containing ONLY closing brackets (and optional whitespace).

**Decision**: Use tokenize module to check if a line contains only OP tokens for closing brackets, INDENT/DEDENT tokens, and whitespace.

**Rationale**:
- The tokenize module already provides token-level granularity
- We can check if the line contains ANY tokens besides closing brackets, whitespace, and comments
- This is more reliable than regex or string parsing

**Implementation Approach**:
```python
def is_bracket_only_line(tokens: list, bracket_token_idx: int) -> bool:
    """Check if the line containing bracket_token has only brackets/whitespace."""
    bracket_token = tokens[bracket_token_idx]
    line_num = bracket_token.start[0]

    # Find all tokens on this line
    line_tokens = [t for t in tokens if t.start[0] == line_num]

    # Filter out NEWLINE, NL, INDENT, DEDENT, COMMENT
    code_tokens = [
        t for t in line_tokens
        if t.type not in (tokenize.NEWLINE, tokenize.NL,
                          tokenize.INDENT, tokenize.DEDENT,
                          tokenize.COMMENT)
    ]

    # Check if all code tokens are closing brackets
    return all(
        t.type == tokenize.OP and t.string in ')}]'
        for t in code_tokens
    )
```

**Alternatives Considered**:
- **Regex on line string**: Match `^\s*[)\]}]+\s*(#.*)?$`. Rejected because it doesn't handle all edge cases (e.g., string literals, escaped characters).
- **Column position check**: Check if bracket is at start of non-whitespace. Rejected because it doesn't work for lines like `  )  )  # comment`.

**Testing Strategy**: Create fixtures with bracket-only lines, mixed code+bracket lines, and verify only bracket-only comments are moved.

---

### 3. BUG 3: `fix-excessive-blank-lines` - Scope to Header Region

**Problem**: Lines 96-114 in the current implementation scan from `header_end` to end of file, collapsing ALL excessive blank lines. The bug is that it should ONLY collapse blank lines between the header and the FIRST line of code, not throughout the entire file.

**Current Logic Analysis** (lines 96-114):
```python
for i in range(header_end, len(lines)):  # BUG: processes entire file
    line = lines[i]
    if line.strip() == "":
        if blank_count == 0:
            start_blank = i
        blank_count += 1
    else:
        # Non-blank line found
        if blank_count >= 2 and start_blank is not None:
            violations.append(...)  # Flags excessive blanks anywhere
        blank_count = 0
```

**Research Task**: Determine the precise region between "end of header" and "first code line" where blank line collapsing should apply.

**Decision**: Only process blank lines from `header_end` until the first non-blank line after the header. Stop processing after that.

**Rationale**:
- The intent is to clean up spacing between file headers (copyright, docstrings) and the actual code
- Blank lines within the code body may be intentional for readability (separating functions, logical blocks)
- The existing `find_module_header_end()` function already identifies where the header ends
- We just need to find the FIRST non-blank line after the header and stop there

**Implementation Approach**:
```python
def fix_file(filename: str) -> None:
    # ... existing code ...

    header_end = find_module_header_end(lines)
    new_lines = lines[:header_end]

    # Find first non-blank line after header
    first_code_line = header_end
    for i in range(header_end, len(lines)):
        if lines[i].strip():
            first_code_line = i
            break

    # Only collapse blanks between header_end and first_code_line
    blank_count = 0
    for i in range(header_end, first_code_line):
        if lines[i].strip() == "":
            blank_count += 1
            if blank_count == 1:
                new_lines.append(lines[i])  # Keep one blank
        # Skip additional blanks

    # Add first code line
    new_lines.append(lines[first_code_line])

    # Keep rest of file unchanged
    new_lines.extend(lines[first_code_line + 1:])
```

**Alternatives Considered**:
- **Apply rule everywhere**: Current behavior. Rejected because it's too aggressive.
- **Use AST to identify function boundaries**: Only collapse blanks outside functions. Rejected because it's more complex and doesn't match the stated intent of the hook.
- **Two-blank-line threshold**: Keep PEP 8's 2-blank-line rule between top-level definitions. Rejected because the hook is specifically about header spacing, not general code formatting.

**Edge Cases to Handle**:
- Files with no header (header_end == 0): Should not modify any blank lines
- Files with only header and no code: Should not modify anything
- Files with header immediately followed by code (no blanks): No changes needed

**Testing Strategy**: Create fixtures with:
- Copyright header + excessive blanks + imports
- No header + code with intentional blanks
- Header + code + functions with intentional spacing

---

## Summary of Research Decisions

| Bug | Approach | Key Module/Pattern | Backward Compatible |
|-----|----------|-------------------|---------------------|
| Ignore Comments | Blacklist of linter pragma patterns | `re` module with pattern list | Yes - only skips moving pragmas |
| Bracket-Only Lines | Token-level analysis to identify bracket-only lines | `tokenize` module with token filtering | Yes - narrows scope of moving |
| Header Blank Lines | Limit scope to header→first-code-line region | Existing `find_module_header_end()` + new logic | Yes - only targets header region |

**Performance Impact**: All changes use standard library modules already in use. No performance degradation expected; may improve performance by reducing scope of operations.

**Testing Impact**: Requires new test fixtures for each bug scenario + edge cases. Estimated ~6 new fixture files and ~6 new test cases.
