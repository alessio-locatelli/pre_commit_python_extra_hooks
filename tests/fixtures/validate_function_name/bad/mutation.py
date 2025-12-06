"""Test fixture: Mutation detection."""


def get_updated(data: dict, key: str, value):
    """Mutate dictionary."""
    data[key] = value
    return data


def get_modified(items: list):
    """Modify list in place."""
    items.append("new")
    return items
