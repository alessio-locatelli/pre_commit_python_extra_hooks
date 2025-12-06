"""Test fixture: Unsafe to auto-fix (large function)."""


def get_user_data(user_id: int):
    """Large function - not safe to auto-fix."""
    # Line 1
    if user_id < 0:
        return None
    # Line 3
    data = {}
    # Line 5
    data["id"] = user_id
    # Line 7
    data["name"] = "User"
    # Line 9
    data["email"] = "user@example.com"
    # Line 11
    data["status"] = "active"
    # Line 13
    data["created"] = "2024-01-01"
    # Line 15
    data["updated"] = "2024-01-01"
    # Line 17
    data["settings"] = {}
    # Line 19: This function is now > 20 lines
    return data
