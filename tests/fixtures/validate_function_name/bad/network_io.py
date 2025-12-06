"""Test fixture: Network I/O detection."""

import requests


def get_api_data(url: str):
    """Fetch data from API."""
    return requests.get(url).json()


def get_posted(data: dict):
    """Send data to server."""
    return requests.post("https://api.example.com", json=data)
