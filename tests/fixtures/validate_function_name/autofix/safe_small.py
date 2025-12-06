"""Test fixture: Safe to auto-fix (small, simple functions)."""

import json


def get_config():
    """Load config - safe to fix."""
    with open("config.json") as f:
        return json.load(f)


def get_active(user: dict) -> bool:
    """Check active - safe to fix."""
    return user.get("status") == "active"


def get_items(data: list):
    """Iterate - safe to fix."""
    for item in data:
        yield item
