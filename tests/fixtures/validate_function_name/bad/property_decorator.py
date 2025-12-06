"""Test fixture: Property decorator detection."""


class MyClass:
    def __init__(self, value: int):
        self._value = value

    @property
    def get_value(self) -> int:
        """Property should not have get_ prefix."""
        return self._value
