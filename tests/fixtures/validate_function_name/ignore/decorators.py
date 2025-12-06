"""Test fixture: Override and abstractmethod decorators."""

from abc import ABC, abstractmethod
from typing import override


class Base(ABC):
    @abstractmethod
    def get_value(self) -> int:
        """Abstract method - should be skipped."""
        pass


class Derived(Base):
    @override
    def get_value(self) -> int:
        """Override - should be skipped."""
        return 42
