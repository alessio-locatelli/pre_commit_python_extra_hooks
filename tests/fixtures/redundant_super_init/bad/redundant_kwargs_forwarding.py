"""Module with redundant kwargs forwarding."""


class Base:
    """Base class that does not accept kwargs."""

    def __init__(self):
        """Initialize base class."""
        self.initialized = True


class Child(Base):
    """Child class that redundantly forwards kwargs."""

    def __init__(self, value, **kwargs):
        """Initialize child."""
        self.value = value
        super().__init__(**kwargs)  # VIOLATION: Parent doesn't accept kwargs
