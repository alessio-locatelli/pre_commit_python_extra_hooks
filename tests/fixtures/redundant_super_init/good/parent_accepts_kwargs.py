"""Module where parent accepts kwargs."""


class Base:
    """Base class that accepts arbitrary arguments."""

    def __init__(self, **kwargs):
        """Initialize with any kwargs."""
        self.config = kwargs


class Child(Base):
    """Child that forwards kwargs to parent."""

    def __init__(self, value, **kwargs):
        """Initialize child."""
        self.value = value
        super().__init__(**kwargs)
