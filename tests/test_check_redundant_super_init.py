"""Tests for check_redundant_super_init hook."""

from pathlib import Path

from pre_commit_hooks.check_redundant_super_init import check_file, main

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


def test_main_cli_with_violations(tmp_path: Path) -> None:
    """Test main() CLI with violations."""
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
    result = main([str(test_file)])
    assert result == 1


def test_main_cli_without_violations(tmp_path: Path) -> None:
    """Test main() CLI without violations."""
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
    result = main([str(test_file)])
    assert result == 0


def test_main_cli_no_files() -> None:
    """Test main() CLI with no files."""
    result = main([])
    assert result == 0


def test_file_io_error(tmp_path: Path) -> None:
    """Test graceful handling of file I/O errors."""
    # Test with non-existent file
    non_existent = tmp_path / "non_existent.py"
    violations = check_file(str(non_existent))
    assert len(violations) == 0


def test_unicode_decode_error(tmp_path: Path) -> None:
    """Test graceful handling of unicode decode errors."""
    # Create a file with invalid UTF-8
    test_file = tmp_path / "bad_encoding.py"
    test_file.write_bytes(b"\xff\xfe\x00\x00")
    violations = check_file(str(test_file))
    assert len(violations) == 0


def test_super_call_without_kwargs_forwarding(tmp_path: Path) -> None:
    """Test super().__init__() call without forwarding kwargs."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self, **kwargs):
        # Call super without forwarding kwargs
        super().__init__()
"""
    )
    violations = check_file(str(test_file))
    # No violation because kwargs are not forwarded
    assert len(violations) == 0


def test_super_call_to_non_init_method(tmp_path: Path) -> None:
    """Test super() call to a method other than __init__."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Base:
    def setup(self):
        pass

class Child(Base):
    def __init__(self, **kwargs):
        super().setup(**kwargs)
"""
    )
    violations = check_file(str(test_file))
    # No violation because it's not a super().__init__() call
    assert len(violations) == 0


def test_parent_with_multiple_positional_args(tmp_path: Path) -> None:
    """Test parent __init__ with multiple positional arguments."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Base:
    def __init__(self, arg1, arg2):
        pass

class Child(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""
    )
    violations = check_file(str(test_file))
    # No violation because parent accepts multiple args
    assert len(violations) == 0


def test_inheritance_chain_no_args(tmp_path: Path) -> None:
    """Test inheritance chain where no ancestor accepts args."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class GrandParent:
    pass

class Parent(GrandParent):
    pass

class Child(Parent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""
    )
    violations = check_file(str(test_file))
    # Violation because no ancestor defines __init__ with args
    assert len(violations) == 1


def test_base_class_not_ast_name(tmp_path: Path) -> None:
    """Test handling of base classes that are not simple names (e.g., module.Class)."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """import module

class Child(module.Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""
    )
    violations = check_file(str(test_file))
    # No violation because we can't analyze imported module.Base
    assert len(violations) == 0


def test_direct_parent_init_call(tmp_path: Path) -> None:
    """Test case where parent __init__ is called directly instead of via super()."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self, **kwargs):
        # Calling parent __init__ directly instead of via super()
        Base.__init__(self, **kwargs)
"""
    )
    violations = check_file(str(test_file))
    # No violation because this isn't a super().__init__() call pattern
    assert len(violations) == 0


def test_parent_with_complex_base(tmp_path: Path) -> None:
    """Test parent class with non-simple base (e.g., module.Class)."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """import module

class Parent(module.SomeBase):
    pass

class Child(Parent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
"""
    )
    violations = check_file(str(test_file))
    # Violation reported because we can't analyze module.SomeBase
    # This is conservative behavior - assumes unknown bases don't accept args
    assert len(violations) == 1
    assert "Parent.__init__()" in violations[0][1]
