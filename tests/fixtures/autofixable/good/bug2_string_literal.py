"""Test case for Bug 2: String literal content should not be modified.

Only the variable assignment should be fixed, not string content.
"""

data = "test"
print("some data here")
message = "data is important"
