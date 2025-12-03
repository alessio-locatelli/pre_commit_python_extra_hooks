"""Test case for Bug 1: Redundant suffix generation.

The hook should suggest 'response', not 'response_2' since there's no conflict.
"""
import request

# Bug: Hook suggests response_2 even though response is not in scope
result = request.get()
answer = result["test"]
