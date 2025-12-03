"""Test fixture for comments on bracket-only lines that SHOULD be moved."""

# Example 1: Comment on line with only closing paren
foo = (
    "bar",
)  # Comment on a wrong line (only closing paren)

# Example 2: Comment on line with only closing bracket
items = [
    "first",
    "second",
]  # This should be moved

# Example 3: Comment on line with only closing brace
data = {
    "key": "value",
}  # Comment misplaced on bracket-only line

# Example 4: Mixed closing brackets (edge case from spec)
nested = (
    [
        {"inner": "value"},
    ],
)  # Multiple brackets with comment

# Example 5: Multiple closing brackets on same line
result = (
    [1, 2, 3],
)  # Comment after multiple bracket types

# Example 6: From bugs_report.md - the exact bug scenario
words = (
    "test",
)  # All synonyms are stored here to prevent duplicates
synonyms: set[str] = set()
