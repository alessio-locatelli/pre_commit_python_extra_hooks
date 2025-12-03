"""Test case for Bug 2: Keyword argument names should not be renamed.

Only the variable assignment should be fixed, not the keyword arg name.
"""
import client

data = "compressed"
resp = client.post("/", data=data, headers={})
