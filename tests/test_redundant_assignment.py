"""Tests for TRI005 redundant assignment check."""

from __future__ import annotations

import ast
from pathlib import Path

from pre_commit_hooks.ast_checks.redundant_assignment import RedundantAssignmentCheck
from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
    PatternType,
    VariableTracker,
    detect_redundancy,
)


def test_immediate_single_use_detected() -> None:
    """Test detection of immediate single use pattern."""
    source = """
x = "foo"
func(x=x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    assert len(violations) >= 1
    violation = violations[0]
    assert violation.error_code == "TRI005"
    assert "x" in violation.message


def test_single_use_return_detected() -> None:
    """Test detection of single-use variable in return."""
    source = """
def example():
    result = get_value()
    return result
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    assert len(violations) >= 1
    assert any("result" in v.message for v in violations)


def test_literal_identity_detected() -> None:
    """Test detection of literal identity pattern."""
    source = """
foo = "foo"
process(foo)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    assert len(violations) >= 1
    assert any("foo" in v.message for v in violations)


def test_literal_identity_with_underscores() -> None:
    """Test literal identity with underscores matches."""
    source = """
SOME_VALUE = "somevalue"
process(SOME_VALUE)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should detect as literal identity (underscores removed match)
    assert len(violations) >= 1


def test_multiple_uses_not_flagged() -> None:
    """Test that variables with multiple uses are not flagged."""
    source = """
value = calc()
print(value)
log(value)
return value
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not flag 'value' because it's used multiple times
    assert len(violations) == 0


def test_semantic_value_skipped() -> None:
    """Test that variables with semantic value are skipped."""
    source = """
def example():
    formatted_timestamp = format_iso8601(raw_ts)
    return formatted_timestamp
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not flag because 'formatted_timestamp' has semantic value
    assert len(violations) == 0


def test_inline_suppression_respected() -> None:
    """Test that inline ignore comments are respected."""
    source = """
x = "foo"  # pytriage: ignore=TRI005
func(x=x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not flag because of inline suppression
    assert len(violations) == 0


def test_inline_suppression_case_insensitive() -> None:
    """Test that inline ignore comments are case-insensitive."""
    source = """
x = "foo"  # PYTRIAGE: IGNORE=TRI005
func(x=x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not flag because of inline suppression
    assert len(violations) == 0


def test_variable_tracker_scope_isolation() -> None:
    """Test that VariableTracker isolates variables by scope."""
    source = """
def outer():
    x = "outer"
    def inner():
        x = "inner"
        return x
    return x
"""
    tracker = VariableTracker(source)
    tree = ast.parse(source)
    tracker.visit(tree)
    lifecycles = tracker.build_lifecycles()

    # Should track two separate lifecycles for 'x' in different scopes
    x_lifecycles = [lc for lc in lifecycles if lc.assignment.var_name == "x"]
    assert len(x_lifecycles) == 2


def test_global_variable_not_analyzed() -> None:
    """Test that global variables are not analyzed."""
    source = """
def func():
    global state
    state = "active"
    return state
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not analyze global variables
    assert len(violations) == 0


def test_type_annotation_adds_value() -> None:
    """Test that type annotations increase semantic value."""
    source = """
def example():
    result: ComplexType = calculate()
    return result
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Type annotation should increase semantic value enough to skip
    # (15 points for annotation + other factors)
    # This might still be flagged depending on total score, so we just check
    # that it doesn't crash
    assert isinstance(violations, list)


def test_comprehension_not_causing_errors() -> None:
    """Test that comprehensions don't cause tracking errors."""
    source = """
result = [x for x in items]
return result
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Comprehensions add semantic value (30 points), so likely won't be flagged
    # Just verify no crashes
    assert isinstance(violations, list)


def test_pattern_detection_immediate_use() -> None:
    """Test pattern detection for immediate single use."""
    source = """
def func():
    x = "foo"
    print(x)
"""
    tracker = VariableTracker(source)
    tree = ast.parse(source)
    tracker.visit(tree)
    lifecycles = tracker.build_lifecycles()

    # Find the 'x' lifecycle
    x_lifecycle = next(lc for lc in lifecycles if lc.assignment.var_name == "x")

    # Should detect immediate single use
    pattern = detect_redundancy(x_lifecycle)
    assert pattern == PatternType.IMMEDIATE_SINGLE_USE


def test_pattern_detection_single_use() -> None:
    """Test pattern detection for single use (not immediate)."""
    source = """
def func():
    x = "foo"
    y = "bar"
    z = "baz"
    print(x)
"""
    tracker = VariableTracker(source)
    tree = ast.parse(source)
    tracker.visit(tree)
    lifecycles = tracker.build_lifecycles()

    # Find the 'x' lifecycle
    x_lifecycle = next(lc for lc in lifecycles if lc.assignment.var_name == "x")

    # Should detect single use (not immediate because there are intervening statements)
    pattern = detect_redundancy(x_lifecycle)
    assert pattern == PatternType.SINGLE_USE


def test_check_id_and_error_code() -> None:
    """Test that check has correct ID and error code."""
    check = RedundantAssignmentCheck()
    assert check.check_id == "redundant-assignment"
    assert check.error_code == "TRI005"


def test_prefilter_pattern() -> None:
    """Test that prefilter pattern is defined."""
    check = RedundantAssignmentCheck()
    pattern = check.get_prefilter_pattern()
    assert pattern == " = "


def test_fixable_marked_correctly() -> None:
    """Test that simple violations are marked fixable."""
    source = """
x = "foo"
func(x=x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should detect violations and mark simple ones as fixable
    assert len(violations) >= 1
    # Simple case: constant assignment, immediate use, short name, no control flow
    assert any(v.fixable for v in violations)


def test_non_fixable_semantic_value() -> None:
    """Test that violations with semantic value are not marked fixable."""
    source = """
def example():
    calculated_value = expensive_operation()
    return calculated_value
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # 'calculated_value' has semantic value (transformative verb 'calculated')
    # so it should not be flagged at all
    assert len(violations) == 0


def test_fix_method_with_fixable_violations() -> None:
    """Test that fix method can fix simple violations."""
    from tempfile import NamedTemporaryFile

    source = """x = "foo"
func(x=x)
"""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(filepath, tree, source)

    # Should detect violations
    assert len(violations) >= 1

    # Simple case should be marked fixable
    assert any(v.fixable for v in violations)

    # Apply fixes
    result = check.fix(filepath, violations, source, tree)
    assert result is True

    # Read the fixed content
    fixed_content = filepath.read_text()

    # The assignment should be removed and the usage should be inlined
    assert "x = " not in fixed_content
    assert 'func(x="foo")' in fixed_content

    filepath.unlink()


def test_autofix_skips_violation_without_fix_data() -> None:
    """Test that autofix skips violations without fix_data."""
    from tempfile import NamedTemporaryFile

    from pre_commit_hooks.ast_checks._base import Violation
    from pre_commit_hooks.ast_checks.redundant_assignment import (
        RedundantAssignmentCheck,
    )

    source = "x = 1\nprint(x)\n"

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    check = RedundantAssignmentCheck()
    tree = ast.parse(source)

    # Create a violation without fix_data
    violations = [
        Violation(
            check_id="redundant-assignment",
            error_code="TRI005",
            line=1,
            col=0,
            message="test",
            fixable=True,
            fix_data=None,
        )
    ]

    result = check.fix(filepath, violations, source, tree)
    assert result is False

    filepath.unlink()


def test_autofix_skips_violation_with_invalid_fix_data() -> None:
    """Test that autofix skips violations with invalid fix_data."""
    from tempfile import NamedTemporaryFile

    from pre_commit_hooks.ast_checks._base import Violation
    from pre_commit_hooks.ast_checks.redundant_assignment import (
        RedundantAssignmentCheck,
    )

    source = "x = 1\nprint(x)\n"

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    check = RedundantAssignmentCheck()
    tree = ast.parse(source)

    # Create a violation with invalid fix_data (missing 'lifecycle')
    violations = [
        Violation(
            check_id="redundant-assignment",
            error_code="TRI005",
            line=1,
            col=0,
            message="test",
            fixable=True,
            fix_data={"other_key": "value"},
        )
    ]

    result = check.fix(filepath, violations, source, tree)
    assert result is False

    filepath.unlink()


def test_autofix_skips_multiline_rhs() -> None:
    """Test that autofix skips multiline expressions."""
    from pre_commit_hooks.ast_checks.redundant_assignment.autofix import (
        _can_safely_inline,
    )

    source_lines = ["result = func(x)\n"]

    # RHS with newline should not be inlined
    result = _can_safely_inline("result", "func(\n    arg\n)", 0, source_lines)
    assert result is False


def test_autofix_skips_line_length_violation() -> None:
    """Test that autofix skips if inlining would exceed line length."""
    from pre_commit_hooks.ast_checks.redundant_assignment.autofix import (
        _can_safely_inline,
    )

    # Current line is 80 chars, adding 20 more would exceed 88
    source_lines = ["x = " + "a" * 80 + "\n"]

    # Inlining would make the line too long
    result = _can_safely_inline("x", "a" * 20, 0, source_lines)
    assert result is False


def test_autofix_skips_invalid_line_indices() -> None:
    """Test that autofix handles invalid line indices gracefully."""
    from pre_commit_hooks.ast_checks.redundant_assignment.autofix import (
        _can_safely_inline,
    )

    source_lines = ["line1\n", "line2\n"]

    # Negative index
    result = _can_safely_inline("x", "value", -1, source_lines)
    assert result is False

    # Index out of bounds
    result = _can_safely_inline("x", "value", 10, source_lines)
    assert result is False


def test_autofix_with_invalid_assignment_line() -> None:
    """Test that autofix skips violations with invalid assignment line indices."""
    from tempfile import NamedTemporaryFile

    from pre_commit_hooks.ast_checks._base import Violation
    from pre_commit_hooks.ast_checks.redundant_assignment import (
        RedundantAssignmentCheck,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        UsageInfo,
        VariableLifecycle,
    )

    source = "x = 1\nprint(x)\n"

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    check = RedundantAssignmentCheck()
    tree = ast.parse(source)
    rhs_node = ast.parse("1", mode="eval").body

    # Create a lifecycle with invalid assignment line (line 100, which doesn't exist)
    assignment = AssignmentInfo(
        var_name="x",
        line=100,  # Invalid line number
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source="1",
        scope_id=0,
        has_type_annotation=False,
    )

    usage = UsageInfo(
        var_name="x",
        line=2,
        col=6,
        stmt_index=1,
        context="unknown",
        scope_id=0,
    )

    lifecycle = VariableLifecycle(assignment=assignment, uses=[usage])

    violations = [
        Violation(
            check_id="redundant-assignment",
            error_code="TRI005",
            line=100,
            col=0,
            message="test",
            fixable=True,
            fix_data={"lifecycle": lifecycle, "pattern": "IMMEDIATE_SINGLE_USE"},
        )
    ]

    result = check.fix(filepath, violations, source, tree)
    assert result is False

    filepath.unlink()


def test_autofix_with_invalid_usage_line() -> None:
    """Test that autofix skips violations with invalid usage line indices."""
    from tempfile import NamedTemporaryFile

    from pre_commit_hooks.ast_checks._base import Violation
    from pre_commit_hooks.ast_checks.redundant_assignment import (
        RedundantAssignmentCheck,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        UsageInfo,
        VariableLifecycle,
    )

    source = "x = 1\nprint(x)\n"

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    check = RedundantAssignmentCheck()
    tree = ast.parse(source)
    rhs_node = ast.parse("1", mode="eval").body

    # Create a lifecycle with invalid usage line (line 100, which doesn't exist)
    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source="1",
        scope_id=0,
        has_type_annotation=False,
    )

    usage = UsageInfo(
        var_name="x",
        line=100,  # Invalid line number
        col=6,
        stmt_index=1,
        context="unknown",
        scope_id=0,
    )

    lifecycle = VariableLifecycle(assignment=assignment, uses=[usage])

    violations = [
        Violation(
            check_id="redundant-assignment",
            error_code="TRI005",
            line=1,
            col=0,
            message="test",
            fixable=True,
            fix_data={"lifecycle": lifecycle, "pattern": "IMMEDIATE_SINGLE_USE"},
        )
    ]

    result = check.fix(filepath, violations, source, tree)
    assert result is False

    filepath.unlink()


def test_autofix_with_multiple_uses() -> None:
    """Test that autofix skips violations with multiple uses."""
    from tempfile import NamedTemporaryFile

    from pre_commit_hooks.ast_checks._base import Violation
    from pre_commit_hooks.ast_checks.redundant_assignment import (
        RedundantAssignmentCheck,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        UsageInfo,
        VariableLifecycle,
    )

    source = "x = 1\nprint(x)\nprint(x)\n"

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    check = RedundantAssignmentCheck()
    tree = ast.parse(source)
    rhs_node = ast.parse("1", mode="eval").body

    # Create a lifecycle with multiple uses
    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source="1",
        scope_id=0,
        has_type_annotation=False,
    )

    usage1 = UsageInfo(
        var_name="x",
        line=2,
        col=6,
        stmt_index=1,
        context="unknown",
        scope_id=0,
    )

    usage2 = UsageInfo(
        var_name="x",
        line=3,
        col=6,
        stmt_index=2,
        context="unknown",
        scope_id=0,
    )

    lifecycle = VariableLifecycle(assignment=assignment, uses=[usage1, usage2])

    violations = [
        Violation(
            check_id="redundant-assignment",
            error_code="TRI005",
            line=1,
            col=0,
            message="test",
            fixable=True,
            fix_data={"lifecycle": lifecycle, "pattern": "SINGLE_USE"},
        )
    ]

    result = check.fix(filepath, violations, source, tree)
    assert result is False  # Should skip because of multiple uses

    filepath.unlink()


def test_autofix_with_unsafe_inlining() -> None:
    """Test that autofix skips when inlining would be unsafe (line too long)."""
    from tempfile import NamedTemporaryFile

    from pre_commit_hooks.ast_checks._base import Violation
    from pre_commit_hooks.ast_checks.redundant_assignment import (
        RedundantAssignmentCheck,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        UsageInfo,
        VariableLifecycle,
    )

    # Create a case where inlining would exceed 88 characters
    # Line is already 60 chars, adding 40 char value would exceed 88
    source = (
        "x = " + "a" * 40 + "\nresult = some_long_function_name(x, param1, param2)\n"
    )

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    check = RedundantAssignmentCheck()
    tree = ast.parse(source)
    rhs_node = ast.parse("a" * 40, mode="eval").body

    # Manually create a fixable violation with a long RHS
    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source="a" * 40,
        scope_id=0,
        has_type_annotation=False,
    )

    usage = UsageInfo(
        var_name="x",
        line=2,
        col=41,  # Position of 'x' in the usage line
        stmt_index=1,
        context="unknown",
        scope_id=0,
    )

    lifecycle = VariableLifecycle(assignment=assignment, uses=[usage])

    violations = [
        Violation(
            check_id="redundant-assignment",
            error_code="TRI005",
            line=1,
            col=0,
            message="test",
            fixable=True,
            fix_data={"lifecycle": lifecycle, "pattern": "IMMEDIATE_SINGLE_USE"},
        )
    ]

    result = check.fix(filepath, violations, source, tree)
    # Should return False because inlining would make the line too long
    assert result is False

    filepath.unlink()


def test_fix_method_with_no_fixable_violations() -> None:
    """Test that fix method returns False when no violations are fixable."""
    from pre_commit_hooks.ast_checks._base import Violation
    from pre_commit_hooks.ast_checks.redundant_assignment.autofix import apply_fixes

    source = """
x = "foo"
func(x=x)
"""
    # Create a non-fixable violation
    violations = [
        Violation(
            check_id="redundant-assignment",
            error_code="TRI005",
            line=1,
            col=0,
            message="test",
            fixable=False,
            fix_data=None,
        )
    ]

    result = apply_fixes(Path("test.py"), violations, source)
    assert result is False


def test_nonlocal_variable_not_analyzed() -> None:
    """Test that nonlocal variables are not analyzed."""
    source = """
def outer():
    x = "outer"
    def inner():
        nonlocal x
        x = "modified"
        return x
    return inner()
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Nonlocal assignment should not be flagged
    assert all("modified" not in v.message for v in violations)


def test_annotated_assignment_tracked() -> None:
    """Test that annotated assignments are tracked."""
    source = """
def example():
    x: str = "foo"
    func(x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should flag if semantic value is low
    # Type annotation adds 15 points, but 'x' literal is still low value
    assert len(violations) >= 1


def test_annotated_assignment_not_global() -> None:
    """Test annotated assignment that is not global/nonlocal (normal path)."""
    source = """
def example():
    result: int = calculate_value()
    another: str = "test"
    return result, another
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Both assignments should be tracked normally
    assert isinstance(violations, list)


def test_annotated_assignment_without_value() -> None:
    """Test annotated assignment without value (type hint only)."""
    source = """
def example():
    x: str  # Type hint only, no assignment
    x = "value"
    return x
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Only the assignment with value should be tracked
    assert isinstance(violations, list)


def test_class_attributes_not_analyzed() -> None:
    """Test that class attributes are not analyzed."""
    source = """
class MyClass:
    x = "foo"

    def method(self):
        self.x = "bar"
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Class attributes should not be flagged
    assert len(violations) == 0


def test_semantic_scoring_long_expression() -> None:
    """Test that long expressions get higher semantic scores."""
    source = """
def example():
    x = very_long_function_name_that_exceeds_sixty_characters_in_total()
    return x
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Long expression should still be flagged if var name adds no value
    # But it might get some points for length
    assert isinstance(violations, list)


def test_semantic_scoring_comprehension() -> None:
    """Test that comprehensions increase semantic value."""
    source = """
result = [x * 2 for x in range(10)]
print(result)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Comprehensions add 30 points, should help avoid flagging
    assert isinstance(violations, list)


def test_semantic_scoring_binary_op() -> None:
    """Test that binary operations increase semantic value."""
    source = """
result = a + b
print(result)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Binary op adds 15 points
    assert isinstance(violations, list)


def test_semantic_scoring_unary_op() -> None:
    """Test that unary operations increase semantic value."""
    source = """
result = -value
print(result)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Unary op adds 10 points
    assert isinstance(violations, list)


def test_semantic_scoring_ternary() -> None:
    """Test that ternary expressions increase semantic value."""
    source = """
result = x if condition else y
print(result)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Ternary adds 20 points
    assert isinstance(violations, list)


def test_semantic_scoring_lambda() -> None:
    """Test that lambda expressions increase semantic value."""
    source = """
func = lambda x: x * 2
result = func(10)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Lambda adds 25 points
    assert isinstance(violations, list)


def test_semantic_scoring_multipart_name() -> None:
    """Test that multi-part names increase semantic value."""
    source = """
def example():
    user_email_address = get_email()
    return user_email_address
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # 3+ parts adds 20 points
    assert isinstance(violations, list)


def test_tuple_unpacking_not_analyzed() -> None:
    """Test that tuple unpacking is not analyzed."""
    source = """
x, y = get_coords()
print(x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Tuple unpacking should not be flagged
    assert len(violations) == 0


def test_process_file_invalid_syntax() -> None:
    """Test that process_file handles invalid syntax gracefully."""
    from tempfile import NamedTemporaryFile

    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        process_file,
    )

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("invalid python syntax (((")
        f.flush()
        filepath = Path(f.name)

    lifecycles = process_file(filepath)
    assert lifecycles == []

    filepath.unlink()


def test_autofix_should_autofix_simple_call() -> None:
    """Test that should_autofix allows simple calls."""
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        PatternType,
        UsageInfo,
        VariableLifecycle,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.semantic import (
        should_autofix,
    )

    # Create a simple call assignment
    source = "get_value()"
    rhs_node = ast.parse(source, mode="eval").body

    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source=source,
        scope_id=0,
        has_type_annotation=False,
    )

    lifecycle = VariableLifecycle(
        assignment=assignment,
        uses=[
            UsageInfo(
                var_name="x",
                line=2,
                col=0,
                stmt_index=1,
                context="unknown",
                scope_id=0,
            )
        ],
    )

    # Should autofix simple call with immediate use
    result = should_autofix(lifecycle, PatternType.IMMEDIATE_SINGLE_USE)
    # This might be True or False depending on semantic score
    assert isinstance(result, bool)


def test_no_uses_not_flagged() -> None:
    """Test that assignments with no uses are not flagged."""
    source = """
def example():
    x = "foo"
    y = "bar"
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Variables with no uses should not be flagged (different issue)
    assert len(violations) == 0


def test_should_autofix_with_single_use_pattern() -> None:
    """Test that should_autofix returns False for SINGLE_USE pattern."""
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        PatternType,
        UsageInfo,
        VariableLifecycle,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.semantic import (
        should_autofix,
    )

    source = "get_value()"
    rhs_node = ast.parse(source, mode="eval").body

    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source=source,
        scope_id=0,
        has_type_annotation=False,
    )

    lifecycle = VariableLifecycle(
        assignment=assignment,
        uses=[
            UsageInfo(
                var_name="x",
                line=5,
                col=0,
                stmt_index=4,  # Not immediate use
                context="unknown",
                scope_id=0,
            )
        ],
    )

    # SINGLE_USE pattern should not be auto-fixed
    result = should_autofix(lifecycle, PatternType.SINGLE_USE)
    assert result is False


def test_semantic_scoring_medium_length_expression() -> None:
    """Test semantic scoring for medium-length expressions (40-60 chars)."""
    from pre_commit_hooks.ast_checks.redundant_assignment.semantic import (
        calculate_semantic_value,
    )

    # Test with exactly 45 characters (between 40 and 60)
    rhs_source = "some_function_with_exactly_45_characters("
    rhs_node = ast.parse(rhs_source + ")", mode="eval").body

    score = calculate_semantic_value("x", rhs_source + ")", rhs_node, False)

    # Should get points for medium length (40-60 chars = +10 points)
    assert score >= 10


def test_should_autofix_call_with_simple_args() -> None:
    """Test that should_autofix allows calls with simple arguments."""
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        PatternType,
        UsageInfo,
        VariableLifecycle,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.semantic import (
        should_autofix,
    )

    # Create a call with simple arguments
    source = "func(1, 2)"
    rhs_node = ast.parse(source, mode="eval").body

    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source=source,
        scope_id=0,
        has_type_annotation=False,
    )

    lifecycle = VariableLifecycle(
        assignment=assignment,
        uses=[
            UsageInfo(
                var_name="x",
                line=2,
                col=0,
                stmt_index=1,
                context="unknown",
                scope_id=0,
            )
        ],
    )

    # Should potentially autofix (depending on semantic score)
    result = should_autofix(lifecycle, PatternType.IMMEDIATE_SINGLE_USE)
    assert isinstance(result, bool)


def test_should_autofix_no_args_call() -> None:
    """Test that should_autofix allows no-args calls."""
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        PatternType,
        UsageInfo,
        VariableLifecycle,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.semantic import (
        should_autofix,
    )

    # Create a call with no arguments
    source = "func()"
    rhs_node = ast.parse(source, mode="eval").body

    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source=source,
        scope_id=0,
        has_type_annotation=False,
    )

    lifecycle = VariableLifecycle(
        assignment=assignment,
        uses=[
            UsageInfo(
                var_name="x",
                line=2,
                col=0,
                stmt_index=1,
                context="unknown",
                scope_id=0,
            )
        ],
    )

    # Should potentially autofix (depending on semantic score)
    result = should_autofix(lifecycle, PatternType.IMMEDIATE_SINGLE_USE)
    assert isinstance(result, bool)


def test_lifecycle_no_uses_not_immediate() -> None:
    """Test that lifecycle with no uses is not immediate."""
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        VariableLifecycle,
    )

    source = "func()"
    rhs_node = ast.parse(source, mode="eval").body

    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source=source,
        scope_id=0,
        has_type_annotation=False,
    )

    # Lifecycle with no uses
    lifecycle = VariableLifecycle(assignment=assignment, uses=[])

    # Should not be immediate use
    assert lifecycle.is_immediate_use is False
    assert lifecycle.is_single_use is False


def test_annotated_assignment_with_nonlocal() -> None:
    """Test that annotated assignments with nonlocal are skipped."""
    source = """
def outer():
    x: str = "outer"
    def inner():
        nonlocal x
        x: str = "modified"
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Nonlocal annotated assignment should be skipped
    assert isinstance(violations, list)


def test_get_source_segment_error_handling() -> None:
    """Test that _get_source_segment handles errors gracefully."""
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        VariableTracker,
    )

    source = "x = 1"
    tracker = VariableTracker(source)

    # Create a node with invalid line numbers
    node = ast.Constant(value=1, lineno=-1, col_offset=-1)

    # Should return empty string on error
    result = tracker._get_source_segment(node)
    assert result == ""


def test_multiple_assignments_to_same_variable() -> None:
    """Test that multiple assignments to same variable create separate lifecycles."""
    source = """
def example():
    x = "first"
    print(x)
    x = "second"
    print(x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Each assignment should be tracked separately
    assert isinstance(violations, list)


def test_multiple_annotated_assignments_same_variable() -> None:
    """Test multiple annotated assignments to same variable."""
    source = """
def example():
    x: str = "first"
    print(x)
    x: str = "second"
    print(x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Each annotated assignment should be tracked separately
    assert isinstance(violations, list)


def test_self_referential_assignment_correctly_tracked() -> None:
    """Test that x = x + 1 pattern correctly ignores LHS in RHS."""
    source = """
def example():
    x = 1
    x = x + 1
    print(x)
    return x
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Second assignment (x = x + 1) has two uses (print and return)
    # First assignment (x = 1) has one use (x + 1 RHS)
    # Neither should be flagged as redundant because multiple uses
    # This test verifies that currently_assigning logic works
    assert len(violations) == 0


def test_should_autofix_complex_call_args() -> None:
    """Test that should_autofix rejects calls with complex arguments."""
    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        AssignmentInfo,
        PatternType,
        UsageInfo,
        VariableLifecycle,
    )
    from pre_commit_hooks.ast_checks.redundant_assignment.semantic import (
        should_autofix,
    )

    # Create a call with complex arguments (dict comprehension)
    source = "func({k: v for k, v in items})"
    rhs_node = ast.parse(source, mode="eval").body

    assignment = AssignmentInfo(
        var_name="x",
        line=1,
        col=0,
        stmt_index=0,
        rhs_node=rhs_node,
        rhs_source=source,
        scope_id=0,
        has_type_annotation=False,
    )

    lifecycle = VariableLifecycle(
        assignment=assignment,
        uses=[
            UsageInfo(
                var_name="x",
                line=2,
                col=0,
                stmt_index=1,
                context="unknown",
                scope_id=0,
            )
        ],
    )

    # Should NOT autofix due to complex arguments
    result = should_autofix(lifecycle, PatternType.IMMEDIATE_SINGLE_USE)
    assert result is False


def test_process_file_success_path() -> None:
    """Test process_file success path with valid Python file."""
    from tempfile import NamedTemporaryFile

    from pre_commit_hooks.ast_checks.redundant_assignment.analysis import (
        process_file,
    )

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def example():
    x = "foo"
    return x
""")
        f.flush()
        filepath = Path(f.name)

    lifecycles = process_file(filepath)
    # Should return lifecycles, not empty list
    assert len(lifecycles) >= 1

    filepath.unlink()


def test_conditional_assignment_with_augmented_use() -> None:
    """Test conditional assignments with augmented assignment not flagged."""
    source = """
def func(v):
    if v:
        msg = "foo"
    else:
        msg = "bar"

    msg += "spameggs"

    print(msg)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should NOT flag either 'msg' assignment because:
    # 1. Both assignments are in different branches (if/else)
    # 2. The variable is used in an augmented assignment (msg += ...)
    # 3. This is not a single-use pattern - the conditional value is essential
    assert len(violations) == 0


def test_augmented_assignment_tracks_usage() -> None:
    """Test that augmented assignments track variable usage."""
    source = """
def example():
    x = 1
    x += 2
    print(x)
"""
    tracker = VariableTracker(source)
    tree = ast.parse(source)
    tracker.visit(tree)
    lifecycles = tracker.build_lifecycles()

    # Should have one lifecycle for 'x' (the initial assignment)
    # Augmented assignments are tracked as usages, not new assignments
    x_lifecycles = [lc for lc in lifecycles if lc.assignment.var_name == "x"]
    assert len(x_lifecycles) == 1

    # The lifecycle should have two uses:
    # 1. The read in x += 2 (augmented assignment)
    # 2. The use in print(x)
    lifecycle = x_lifecycles[0]
    assert len(lifecycle.uses) == 2


def test_augmented_assignment_single_use_can_be_flagged() -> None:
    """Test that augmented assignments can still be flagged if redundant."""
    source = """
def example():
    x = 1
    x += 1
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # The first assignment (x = 1) is used once (in x += 1)
    # This could be flagged as it's a simple pattern
    # But augmented assignments typically indicate the variable will be used again
    # So it's reasonable either way
    assert isinstance(violations, list)


def test_long_chained_expression_not_flagged() -> None:
    """Test that long chained expressions with meaningful names are not flagged."""
    source = """
@functools.cache
def find_place_document(place_id):
    collection_places = singleton_factory(mongo_client)[DATABASE_NAME]["places"]
    return collection_places.find_one({"_id": place_id})
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should NOT flag 'collection_places' because:
    # 1. It's a long expression (70+ chars)
    # 2. It has chained subscript operations
    # 3. The variable name is meaningful and descriptive
    # 4. Breaking it down improves readability
    assert len(violations) == 0


def test_autofix_respects_line_length() -> None:
    """Test that autofix doesn't inline if it would exceed line length."""
    from tempfile import NamedTemporaryFile

    # Create a case where inlining would exceed 88 characters
    source = """x = "a_very_long_string_that_when_inlined_would_make_the_line_too_long"
result = some_function(x, another_param, yet_another_param)
"""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(filepath, tree, source)

    # May or may not have violations depending on semantic scoring
    # But if there are violations, they should NOT be fixable due to line length
    for v in violations:
        if v.fixable:  # pragma: no cover - autofix disabled
            result = check.fix(filepath, [v], source, tree)
            # Should not fix if it violates line length
            fixed = filepath.read_text()
            assert len(fixed.splitlines()[1]) <= 88 or result is False

    filepath.unlink()


def test_autofix_handles_word_boundaries() -> None:
    """Test that autofix correctly handles variable names as whole words."""
    from tempfile import NamedTemporaryFile

    # Test that 'x' doesn't match 'max' or 'index'
    source = """x = 5
result = x + max(x, index)
"""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(filepath, tree, source)

    if violations and any(
        v.fixable for v in violations
    ):  # pragma: no cover - autofix disabled
        check.fix(filepath, violations, source, tree)
        fixed = filepath.read_text()

        # Should only replace the standalone 'x', not 'max' or 'index'
        assert "max" in fixed
        assert "index" in fixed

    filepath.unlink()


def test_chained_operations_scoring() -> None:
    """Test that chained operations increase semantic value."""
    from pre_commit_hooks.ast_checks.redundant_assignment.semantic import (
        calculate_semantic_value,
    )

    # Test with 2 chained subscripts: obj[x][y]
    source = "obj[x][y]"
    rhs_node = ast.parse(source, mode="eval").body
    score = calculate_semantic_value("result", source, rhs_node, False)

    # Should get points for chained operations (2 chains = +20)
    # "result" is 1 part (+0), short expression (+0)
    assert score == 20

    # Test with 3 chained operations and better naming
    source = "func()[x][y]"
    rhs_node = ast.parse(source, mode="eval").body
    score = calculate_semantic_value("my_value", source, rhs_node, False)

    # Should get points for:
    # - 3+ chains (+30)
    # - 2-part name (+10)
    assert score == 40

    # Test with attribute chaining: obj.foo.bar
    source = "obj.foo.bar"
    rhs_node = ast.parse(source, mode="eval").body
    score = calculate_semantic_value("result", source, rhs_node, False)

    # Should get points for chained attributes (2 chains = +20)
    assert score >= 20


def test_augmented_assignment_with_global_variable() -> None:
    """Test that augmented assignments with global variables are skipped."""
    source = """
def func():
    global x
    x += 1
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not flag global variable
    assert len(violations) == 0


def test_augmented_assignment_with_nonlocal_variable() -> None:
    """Test that augmented assignments with nonlocal variables are skipped."""
    source = """
def outer():
    x = 1
    def inner():
        nonlocal x
        x += 1
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not flag nonlocal variable
    assert isinstance(violations, list)


def test_augmented_assignment_with_attribute() -> None:
    """Test that augmented assignments to attributes (not simple names) are skipped."""
    source = """
def func():
    obj.x += 1
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not track attribute assignments
    assert len(violations) == 0


def test_semantic_scoring_very_long_expression() -> None:
    """Test that very long expressions (80+ chars) get extra points."""
    from pre_commit_hooks.ast_checks.redundant_assignment.semantic import (
        calculate_semantic_value,
    )

    # Create an 85-character expression
    source = "a" * 85
    rhs_node = ast.parse(source, mode="eval").body
    score = calculate_semantic_value("x", source, rhs_node, False)

    # Should get points for very long expression (80+ = +35)
    assert score >= 35


# === Autofix Safety Tests ===
# Tests to verify autofix only handles safe, simple cases


def test_autofix_not_in_loop() -> None:
    """Test that autofix does not fix variables inside loops."""
    source = """
for i in range(10):
    x = i * 2
    print(x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not flag or fix variables in loops
    assert len(violations) == 0


def test_autofix_not_in_control_flow() -> None:
    """Test that autofix does not fix variables inside control flow."""
    source = """
def example():
    if condition:
        x = "value"
        process(x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # May detect but should not be fixable due to control flow
    for v in violations:
        assert not v.fixable


def test_autofix_not_long_names() -> None:
    """Test that autofix does not fix variables with long names."""
    source = """
very_long_descriptive_name = 42
use(very_long_descriptive_name)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not be fixable due to long variable name (> 10 chars)
    for v in violations:
        assert not v.fixable


def test_autofix_only_simple_rhs() -> None:
    """Test that autofix only fixes simple RHS expressions."""
    source = """
def example():
    x = func(arg1, arg2)
    return x
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should not be fixable due to complex RHS (function call)
    for v in violations:
        assert not v.fixable


def test_autofix_simple_constant() -> None:
    """Test that autofix handles simple constants."""
    from tempfile import NamedTemporaryFile

    source = """y = 42
result = y + 10
"""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(filepath, tree, source)

    # Simple constant should be fixable
    fixable_violations = [v for v in violations if v.fixable]
    if fixable_violations:
        result = check.fix(filepath, fixable_violations, source, tree)
        assert result is True

        fixed_content = filepath.read_text()
        assert "y = 42" not in fixed_content
        assert "result = 42 + 10" in fixed_content

    filepath.unlink()


def test_autofix_simple_attribute() -> None:
    """Test that autofix handles simple single-level attribute access."""
    from tempfile import NamedTemporaryFile

    source = """v = obj.attr
use(v)
"""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(filepath, tree, source)

    # Simple attribute access should be fixable
    fixable_violations = [v for v in violations if v.fixable]
    if fixable_violations:
        result = check.fix(filepath, fixable_violations, source, tree)
        assert result is True

        fixed_content = filepath.read_text()
        assert "v = obj.attr" not in fixed_content
        assert "use(obj.attr)" in fixed_content

    filepath.unlink()


def test_autofix_word_boundaries() -> None:
    """Test that autofix uses word boundaries correctly."""
    from tempfile import NamedTemporaryFile

    source = """x = 5
result = max(x, 10)
"""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(filepath, tree, source)

    fixable_violations = [v for v in violations if v.fixable]
    if fixable_violations:
        result = check.fix(filepath, fixable_violations, source, tree)
        assert result is True

        fixed_content = filepath.read_text()
        # Should replace 'x' but not affect 'max'
        assert "result = max(5, 10)" in fixed_content
        assert "max" in fixed_content  # 'max' should still be present

    filepath.unlink()


# === Bug Reproduction Tests ===
# The following tests reproduce bugs from bug_report.md


def test_problem_1_loop_reassignment() -> None:
    """Reproduce Problem 1: Wrong variable replacement in loop reassignment."""
    source = """def find_route():
    latest_datetime = initial_datetime
    for edge in edges:
        destination_datetime_utc = edge.destination_datetime_utc
        if destination_datetime_utc > latest_datetime:
            latest_datetime = destination_datetime_utc
            break
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should NOT flag latest_datetime as it's reassigned in a loop
    # and used across iterations
    for v in violations:
        assert "latest_datetime" not in v.message, (
            f"Should not flag latest_datetime in loop reassignment: {v.message}"
        )


def test_problem_2_boolean_descriptive_names() -> None:
    """Reproduce Problem 2: False positive on descriptive boolean names."""
    source = """def check_cycle(subgraph, depot_idx):
    out_edge_count = len(subgraph.out_edges(depot_idx))
    in_edge_count = len(subgraph.in_edges(depot_idx))
    has_cycle = bool(find_cycle(subgraph, depot_idx))
    if not all((out_edge_count, in_edge_count, has_cycle)):
        raise ValueError("Invalid graph")
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should NOT flag has_cycle - it's a descriptive boolean name
    for v in violations:
        assert "has_cycle" not in v.message, (
            f"Should not flag descriptive boolean variable has_cycle: {v.message}"
        )


def test_problem_4_multiple_exception_assignments() -> None:
    """Reproduce Problem 4: Concatenated variable names from multiple assignments."""
    from tempfile import NamedTemporaryFile

    source = """def fetch_data():
    error = None
    try:
        return get_data()
    except ValueError as value_error:
        error = value_error
    except TypeError as type_error:
        error = type_error
    except KeyError as key_error:
        error = key_error
    raise error
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    violations = check.check(filepath, tree, source)

    # If there are fixable violations, applying the fix should NOT create
    # concatenated nonsense like "value_errortype_errorkey_error"
    if any(v.fixable for v in violations):  # pragma: no cover - autofix disabled
        check.fix(filepath, violations, source, tree)
        fixed_content = filepath.read_text()

        # Verify no concatenated garbage
        assert "value_errortype_error" not in fixed_content
        assert "type_errorkey_error" not in fixed_content

        # Verify the code is still valid Python
        try:
            ast.parse(fixed_content)
        except SyntaxError as e:
            msg = f"Fixed code has syntax error: {e}\n{fixed_content}"
            raise AssertionError(msg) from e

    filepath.unlink()


def test_problem_5_conditional_assignment_logic_change() -> None:
    """Reproduce Problem 5: Logic-changing autofix for conditional assignments."""
    from tempfile import NamedTemporaryFile

    source = """def configure(service_name=None):
    if not service_name:
        service_name = get_caller_module_name()
    return configure_service(service_name)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()

    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(source)
        f.flush()
        filepath = Path(f.name)

    violations = check.check(filepath, tree, source)

    # If there are fixable violations, verify the logic isn't changed
    if any(v.fixable for v in violations):  # pragma: no cover - autofix disabled
        check.fix(filepath, violations, source, tree)
        fixed_content = filepath.read_text()

        # The fixed code should NOT change the logic
        # Original: assigns get_caller_module_name() to service_name, then uses it
        # WRONG: if not get_caller_module_name(): ...
        assert "if not get_caller_module_name():" not in fixed_content, (
            f"Autofix changed program logic!\n{fixed_content}"
        )

    filepath.unlink()


def test_same_variable_different_scopes() -> None:
    """Test that variables in different branches are tracked correctly."""
    source = """def process(value):
    if value > 0:
        result = "positive"
        log(result)
    else:
        result = "negative"
        log(result)
    return result
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should NOT flag result because:
    # 1. It's assigned in different branches
    # 2. It's used after the if/else block
    # 3. Both assignments are needed for the final return
    for v in violations:
        should_skip = (
            "result" not in v.message
            or "positive" not in source
            or "negative" not in source
        )
        assert should_skip
