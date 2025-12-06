"""Test fixture: Collection/extraction detection."""

import json


def get_names(users: list[dict]) -> list[str]:
    """Extract names from user list."""
    names = []
    for user in users:
        names.append(user["name"])
    return names


def get_config_values(text: str) -> dict:
    """Parse and collect config values."""
    return json.loads(text)
