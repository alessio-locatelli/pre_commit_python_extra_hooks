"""Test fixture: Delegating getters (should be skipped)."""


def get_actual_value():
    """Helper to fetch value."""
    return 42


def get_value():
    """Delegates to another get_ function."""
    return get_actual_value()


def get_computed():
    """Delegates via variable."""
    result = get_actual_value()
    return result
