"""Test fixture: Parsing detection."""

import json


def get_json_data(text: str):
    """Parse JSON string."""
    return json.loads(text)


def get_rendered(data: dict) -> str:
    """Render data as JSON."""
    return json.dumps(data)
