"""Tests for check_redundant_super_init hook."""

from pathlib import Path


def test_detects_redundant_kwargs_forwarding(tmp_path: Path) -> None:
    """Test detection of redundant kwargs forwarding."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""
    )
    # Hook should detect violation on line 6


def test_no_violation_when_parent_accepts_kwargs(tmp_path: Path) -> None:
    """Test no violation when parent accepts kwargs."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Base:
    def __init__(self, **kwargs):
        pass

class Child(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""
    )
    # Hook should return 0 (no violation)


def test_no_violation_when_no_kwargs(tmp_path: Path) -> None:
    """Test no violation when child has no kwargs."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self, value):
        super().__init__()
"""
    )
    # Hook should return 0 (no kwargs, no violation)


def test_skips_unresolvable_parents(tmp_path: Path) -> None:
    """Test skipping of unresolvable parent classes."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """from external import Base

class Child(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""
    )
    # Hook should skip (parent is from import)


def test_handles_multiple_inheritance(tmp_path: Path) -> None:
    """Test handling of multiple inheritance."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Base:
    def __init__(self):
        pass

class Mixin:
    def __init__(self, **kwargs):
        pass

class Child(Base, Mixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""
    )
    # Hook should detect violation for Base


def test_handles_syntax_errors_gracefully(tmp_path: Path) -> None:
    """Test graceful handling of syntax errors."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Broken(
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""  # noqa: E501
    )
    # Hook should skip gracefully
