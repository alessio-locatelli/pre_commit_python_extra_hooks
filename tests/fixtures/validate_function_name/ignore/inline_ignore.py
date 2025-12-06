"""Test fixture: Inline ignore comments."""


def get_users() -> list:  # naming: ignore
    """Suppressed with inline comment."""
    with open("users.json") as f:
        return f.read()


def get_data():  # naming: ignore
    """Also suppressed."""
    return []
