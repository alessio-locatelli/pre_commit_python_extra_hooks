"""Module with proper signature matching."""


class Base:
    """Base class with kwargs."""

    def __init__(self, **kwargs):
        """Initialize base class."""
        self.kwargs = kwargs


class Child(Base):
    """Child class that properly matches parent signature."""

    def __init__(self, name, **kwargs):
        """Initialize child class."""
        self.name = name
        super().__init__(**kwargs)
