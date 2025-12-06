"""Test fixture: Simple accessors (should be skipped)."""


class MyClass:
    def __init__(self):
        self._value = 42
        self._data = {}

    def get_value(self):
        """Simple accessor - idiomatic getter."""
        return self._value

    def get_data(self):
        """Dict accessor."""
        return self._data

    def get_item(self, key):
        """Subscript accessor."""
        return self._data[key]

    def get_default(self, key, default=None):
        """Dict.get() accessor."""
        return self._data.get(key, default)
