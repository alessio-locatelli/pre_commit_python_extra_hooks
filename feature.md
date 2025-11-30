### STYLE-001: Misplaced comment

**Category:** Style
**Severity:** Low

**Problem:** A comment sits on a line not next to the relevant expression (often from auto-formatting), hurting clarity.

**Bad:**

```python
foobar = Field(
    "42"
)  # Some text explaining why we use this value here.
```

**Good:**

```python
foobar = Field(
    "42"  # Some text explaining why we use this value here.
)
```

```python
foobar = Field(
    # Some text explaining why we use this value here.
    "42"
)
```

#### Automated Refactor Hints

- If a trailing comment is on an empty/closing line, move it to the expression line above.
- Prefer inline comment when the expression is short. Otherwise put a preceding `#` comment on the line above.

### STYLE-002: Too many blank lines

**Category:** Style
**Severity:** Low

**Problem:** Multiple blank lines after module header or top comment.

**Bad:**

```python
# Some text at the top of the file.


from __future__ import annotations
```

**Good:**

```python
# Some text at the top of the file.

from __future__ import annotations
```

#### Notes

A copyright comment must be separated by one blank line from the code that follows it.

```python
# Copyright (c) 2008, John Doe. All rights reserved.
#
# Some optional text related to copyright.

import something
```

#### Automated Refactor Hints

- Collapse runs of 2+ blank lines to a single blank line after top-level comments.

### MAINTAINABILITY-006: Redundant `super().__init__(**kwargs)`

**Category:** Maintainability
**Severity:** Low

**Problem:** Forwarding `**kwargs` to a parent `__init__` that accepts `()` creates misleading chains.

**Bad:**

```python
class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x = 1
```

**Good:**

```python
class Child(Base):
    def __init__(self):
        super().__init__()
        self.x = 1
```

#### Automated Refactor Hints

- Replace `super().__init__(**kwargs)` with `super().__init__()` or remove if parent init is trivial.
