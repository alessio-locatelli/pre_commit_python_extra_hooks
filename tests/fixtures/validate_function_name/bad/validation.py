"""Test fixture: Validation detection."""


def get_errors(data: dict) -> list[str]:
    """Validate input data."""
    errors = []
    if not data.get("name"):
        errors.append("Name required")
    if not data.get("email"):
        errors.append("Email required")
    return errors
