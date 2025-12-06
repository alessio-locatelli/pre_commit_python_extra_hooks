"""Test fixture: Searching/finding detection."""


def get_index(items: list, target):
    """Search for item index."""
    return items.index(target)


def get_match(text: str, pattern: str):
    """Find pattern in text."""
    import re

    return re.search(pattern, text)
