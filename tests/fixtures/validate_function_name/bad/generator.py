"""Test fixture: Generator/yield detection."""


def get_items(data: list):
    """Generate items from list."""
    for item in data:
        yield item


def get_lines(filename: str):
    """Yield lines from file."""
    with open(filename) as f:
        for line in f:
            yield line.strip()
