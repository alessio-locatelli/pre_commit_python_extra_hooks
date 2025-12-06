"""Test fixture: Object creation detection."""


class User:
    def __init__(self, name: str):
        self.name = name


def get_user(name: str) -> User:
    """Create new user instance."""
    return User(name)


def get_instance():
    """Create object."""
    return User("default")
