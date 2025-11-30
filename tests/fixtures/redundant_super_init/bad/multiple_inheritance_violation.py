"""Module with multiple inheritance violation."""


class Base:
    """Base class that does not accept kwargs."""

    def __init__(self):
        """Initialize base class."""
        self.base_init = True


class Mixin:
    """Mixin class."""

    def __init__(self, **kwargs):
        """Initialize mixin."""
        self.mixin_kwargs = kwargs


class Child(Base, Mixin):
    """Child with multiple inheritance."""

    def __init__(self, **kwargs):
        """Initialize child."""
        super().__init__(**kwargs)  # VIOLATION: Base doesn't accept kwargs
