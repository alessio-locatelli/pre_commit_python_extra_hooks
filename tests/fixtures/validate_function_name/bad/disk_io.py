"""Test fixture: Disk I/O detection."""

import json


def get_config():
    """Load configuration from disk."""
    with open("config.json") as f:
        return json.load(f)


def get_data_from_file():
    """Read data from file."""
    return open("data.txt").read()


def get_saved_state(path):
    """Write state to disk."""
    with open(path, "w") as f:
        f.write("state")
    return "saved"
