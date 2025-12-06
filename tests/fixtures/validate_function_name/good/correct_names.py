"""Test fixture: Correctly named functions (no violations)."""

import json


def is_valid(data: str) -> bool:
    """Check if data is valid."""
    return len(data) > 0


def load_config():
    """Load configuration."""
    with open("config.json") as f:
        return json.load(f)


def fetch_data(url: str):
    """Fetch data from API."""
    import requests

    return requests.get(url).json()


def iter_items(data: list):
    """Iterate over items."""
    for item in data:
        yield item


def calculate_total(numbers: list[int]) -> int:
    """Calculate sum."""
    return sum(numbers)


def parse_json(text: str):
    """Parse JSON."""
    return json.loads(text)


def find_match(text: str, pattern: str):
    """Find pattern."""
    import re

    return re.search(pattern, text)


def validate_input(data: dict) -> list[str]:
    """Validate input."""
    errors = []
    if not data.get("name"):
        errors.append("Name required")
    return errors


def extract_names(users: list[dict]) -> list[str]:
    """Extract names."""
    return [u["name"] for u in users]


def create_user(name: str):
    """Create user."""

    class User:
        pass

    return User()


def update_data(data: dict, key: str, value):
    """Update data."""
    data[key] = value
    return data
