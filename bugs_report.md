# `fix-misplaced-comments` bugs

## BUG 1

### Current (wrong)

Ignore comments (`# type: ignore`, `# noqa`, `# pragma`, etc.) are moved to irrelevant lines.

### Expected (correct)

Create a blacklist of common "ignore" comments used by different linters and do not move these comments.

## BUG 2

### Current (wrong)

The valid comment is moved to the wrong location if the code ends with `)`:

```diff
+    # All synonyms are stored here to prevent duplicates
     words = (words,) if isinstance(words, str) else words
-    synonyms: set[str] = set()  # All synonyms are stored here to prevent duplicates
```

### Expected (correct)

Must consider only the comments that are on a line that only contains a bracket.

This is wrong code because the comment is on the line that contains nothing, but only `)`:

```py
foo = (
  "bar",
)  # Comment on a wrong line.
```

This is correct code:

```py
foo = ("bar", "spam")  # Comment on a correct line.
```

Auto-detection pattern: look at the lines that contain only one or more brackets (`)`, `}`, `]`) and a comment on the same line.


# `fix-excessive-blank-lines` bugs


Now: This hook replaces all 2 blank lines with 1 blank line.

Expected: Only replace 2 blank lines with 1 blank line between the top-level comment (e.g., a copyright) and the Python code below.
