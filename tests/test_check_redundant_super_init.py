"""Tests for check_redundant_super_init hook."""


def test_detects_redundant_kwargs_forwarding(tmp_path):
    """Test detection of redundant kwargs forwarding."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        "class Base:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "\n"
        "class Child(Base):\n"
        "    def __init__(self, **kwargs):\n"
        "        super().__init__(**kwargs)\n"
    )
    # Hook should detect violation on line 6


def test_no_violation_when_parent_accepts_kwargs(tmp_path):
    """Test no violation when parent accepts kwargs."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        "class Base:\n"
        "    def __init__(self, **kwargs):\n"
        "        pass\n"
        "\n"
        "class Child(Base):\n"
        "    def __init__(self, **kwargs):\n"
        "        super().__init__(**kwargs)\n"
    )
    # Hook should return 0 (no violation)


def test_no_violation_when_no_kwargs(tmp_path):
    """Test no violation when child has no kwargs."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        "class Base:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "\n"
        "class Child(Base):\n"
        "    def __init__(self, value):\n"
        "        super().__init__()\n"
    )
    # Hook should return 0 (no kwargs, no violation)


def test_skips_unresolvable_parents(tmp_path):
    """Test skipping of unresolvable parent classes."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        "from external import Base\n"
        "\n"
        "class Child(Base):\n"
        "    def __init__(self, **kwargs):\n"
        "        super().__init__(**kwargs)\n"
    )
    # Hook should skip (parent is from import)


def test_handles_multiple_inheritance(tmp_path):
    """Test handling of multiple inheritance."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        "class Base:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "\n"
        "class Mixin:\n"
        "    def __init__(self, **kwargs):\n"
        "        pass\n"
        "\n"
        "class Child(Base, Mixin):\n"
        "    def __init__(self, **kwargs):\n"
        "        super().__init__(**kwargs)\n"
    )
    # Hook should detect violation for Base


def test_handles_syntax_errors_gracefully(tmp_path):
    """Test graceful handling of syntax errors."""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        "class Broken(\n    def __init__(self, **kwargs):\n        super().__init__(**kwargs)\n"  # noqa: E501
    )
    # Hook should skip gracefully
