"""Test fixture: Unsafe to auto-fix (complex control flow)."""


def get_value(data: dict, key: str):
    """Nested conditions - not safe to auto-fix."""
    if key in data:
        value = data[key]
        if isinstance(value, str):  # Nested if (depth > 1)
            return value.upper()
        return value
    return None


def get_result(items: list):
    """Multiple returns - not safe to auto-fix."""
    if not items:
        return None
    if len(items) == 1:
        return items[0]
    return items
