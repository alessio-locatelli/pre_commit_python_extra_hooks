"""Test case for Bug 2: Object attributes should not be renamed.

Only the variable assignment should be fixed, not attribute access.
"""
import api
import msg

result = api.get()
print(msg.result)
