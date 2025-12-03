"""Test case for Bug 2: Function parameters should not be renamed.

Function parameters with forbidden names should be detected but NOT autofixed.
"""

def delay_received(data: bytes) -> None:
    """Process received data."""
    print(data)
