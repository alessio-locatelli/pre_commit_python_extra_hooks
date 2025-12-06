"""Test fixture: Boolean return detection."""


def get_active(user: dict) -> bool:
    """Check if user is active."""
    return user.get("status") == "active"


def get_valid(data: str) -> bool:
    """Validate data format."""
    return len(data) > 0 and data.isalnum()
