"""Tests for check_redundant_super_init hook."""

from pathlib import Path

from pre_commit_hooks.check_redundant_super_init import check_file

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "redundant_super_init"


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
    violations = check_file(str(test_file))
    assert len(violations) == 1
    assert "Redundant **kwargs forwarded" in violations[0][1]


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
    violations = check_file(str(test_file))
    assert len(violations) == 0


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
    violations = check_file(str(test_file))
    assert len(violations) == 0


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
    violations = check_file(str(test_file))
    assert len(violations) == 0


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
    violations = check_file(str(test_file))
    # Base (first parent) doesn't accept kwargs, so violation is reported
    assert len(violations) == 1
    assert "Redundant **kwargs forwarded to Base" in violations[0][1]


def test_handles_syntax_errors_gracefully(tmp_path: Path) -> None:
    """Test graceful handling of syntax errors."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Broken(
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""  # noqa: E501
    )
    violations = check_file(str(test_file))
    assert len(violations) == 0


def test_no_violation_with_inheritance_chain() -> None:
    """Test no violation with aiohttp-style inheritance chain.

    This is the bug fix test case: when a class doesn't define __init__
    but an ancestor does accept **kwargs, the hook should not report
    a false-positive.
    """
    fixture_file = FIXTURES_DIR / "good" / "inheritance_chain_with_kwargs.py"
    violations = check_file(str(fixture_file))
    assert len(violations) == 0, (
        "Inheritance chain with kwargs should not be flagged as violation"
    )
