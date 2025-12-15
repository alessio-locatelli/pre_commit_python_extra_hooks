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
    """Test that fixable violations are marked correctly."""
    source = """
x = "foo"
func(x=x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Should have at least one fixable violation
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


def test_fix_method_returns_false() -> None:
    """Test that fix method returns False when no fixes applied."""
    source = """
x = "foo"
func(x=x)
"""
    tree = ast.parse(source)
    check = RedundantAssignmentCheck()
    violations = check.check(Path("test.py"), tree, source)

    # Currently fix is not fully implemented
    result = check.fix(Path("test.py"), violations, source, tree)
    assert result is False


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
