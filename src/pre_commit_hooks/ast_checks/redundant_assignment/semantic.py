"""Semantic value analysis for variable names in TRI005."""

from __future__ import annotations

import ast

from .analysis import PatternType, VariableLifecycle

# Transformative verbs that indicate semantic value
TRANSFORMATIVE_VERBS = {
    "formatted",
    "parsed",
    "calculated",
    "validated",
    "sanitized",
    "normalized",
    "converted",
    "transformed",
    "processed",
    "filtered",
    "sorted",
    "grouped",
    "aggregated",
    "extracted",
    "compiled",
    "decoded",
    "encoded",
    "serialized",
    "deserialized",
}

# Boolean/descriptive prefixes that indicate semantic value
DESCRIPTIVE_PREFIXES = {
    "has_",
    "is_",
    "should_",
    "can_",
    "will_",
    "did_",
    "was_",
    "are_",
    "were_",
    "does_",
}

# Descriptive suffixes that indicate semantic value
DESCRIPTIVE_SUFFIXES = {
    "_count",
    "_flag",
    "_exists",
    "_found",
    "_valid",
    "_enabled",
    "_disabled",
    "_available",
    "_ready",
}


def _count_chained_operations(node: ast.expr) -> int:
    """Count the number of chained operations (subscripts, attributes, calls).

    Examples:
        foo.bar.baz -> 2 (two attribute accesses)
        obj[x][y][z] -> 3 (three subscripts)
        func()[key].attr -> 2 (subscript + attribute)

    Args:
        node: AST expression node

    Returns:
        Number of chained operations
    """
    count = 0
    current = node

    while True:
        if isinstance(current, ast.Subscript | ast.Attribute):
            count += 1
            current = current.value
        elif isinstance(current, ast.Call):
            # Count the call itself if it's part of a chain
            if count > 0:  # Only count if it's chained with something
                count += 1
            current = current.func
        else:
            # Reached the base of the chain
            break

    return count


def calculate_semantic_value(
    var_name: str,
    rhs_source: str,
    rhs_node: ast.expr,
    has_type_annotation: bool = False,
) -> int:
    """Calculate semantic value score for a variable name.

    The score ranges from 0-100:
    - 0-20: No semantic value (redundant assignment, can auto-fix)
    - 21-49: Marginal value (report but don't auto-fix)
    - 50-100: Clear value (skip entirely)

    Args:
        var_name: Variable name
        rhs_source: Right-hand side source code
        rhs_node: Right-hand side AST node
        has_type_annotation: Whether assignment has type annotation

    Returns:
        Semantic value score (0-100)
    """
    score = 0

    # Check for transformative verbs (+60 points - strong signal of semantic value)
    var_lower = var_name.lower()
    if any(verb in var_lower for verb in TRANSFORMATIVE_VERBS):
        score += 60

    # Check for descriptive boolean prefixes (+50 points - strong signal)
    if any(var_lower.startswith(prefix) for prefix in DESCRIPTIVE_PREFIXES):
        score += 50

    # Check for descriptive suffixes (+40 points)
    if any(var_lower.endswith(suffix) for suffix in DESCRIPTIVE_SUFFIXES):
        score += 40

    # Expression complexity scoring
    if isinstance(
        rhs_node, ast.ListComp | ast.DictComp | ast.SetComp | ast.GeneratorExp
    ):
        # Comprehensions benefit from naming (+30)
        score += 30
    elif isinstance(rhs_node, ast.BinOp):
        # Binary operations (+15)
        score += 15
    elif isinstance(rhs_node, ast.UnaryOp):
        # Unary operations (+10)
        score += 10
    elif isinstance(rhs_node, ast.IfExp):
        # Ternary expressions (+20)
        score += 20
    elif isinstance(rhs_node, ast.Lambda):
        # Lambda expressions (+25)
        score += 25

    # Chained operations benefit significantly from naming
    # Examples: obj[x][y], foo.bar.baz, func()[key].attr
    chain_count = _count_chained_operations(rhs_node)
    if chain_count >= 3:
        # 3+ chained operations are hard to read inline (+30)
        score += 30
    elif chain_count == 2:
        # 2 chained operations benefit from naming (+20)
        score += 20

    # Long expressions benefit from naming (progressive scoring)
    if len(rhs_source) > 80:
        # Very long expressions (80+) strongly benefit from naming
        score += 35
    elif len(rhs_source) > 60:
        # Long expressions (60-80) benefit from naming
        score += 25
    elif len(rhs_source) > 40:
        # Medium expressions (40-60) somewhat benefit
        score += 10

    # Multi-part names often represent domain concepts
    name_parts = var_name.split("_")
    if len(name_parts) >= 3:
        # 3+ parts suggests domain-specific naming
        score += 20
    elif len(name_parts) == 2:
        # 2 parts is moderate
        score += 10

    # Variable name significantly longer than expression
    if len(var_name) > len(rhs_source) * 1.3:
        score += 15
    elif len(var_name) > len(rhs_source) * 1.1:
        score += 5

    # Type annotations add clarity
    if has_type_annotation:
        score += 15

    # Cap at 100
    return min(score, 100)


def should_report_violation(
    lifecycle: VariableLifecycle,
    pattern: PatternType,
) -> bool:
    """Determine if a violation should be reported based on semantic analysis.

    Args:
        lifecycle: Variable lifecycle
        pattern: Detected pattern type

    Returns:
        True if violation should be reported
    """
    assignment = lifecycle.assignment

    # Don't report assignments inside loops - they often accumulate/track state
    # across iterations even if they appear to have single use per iteration
    if assignment.in_loop:
        return False

    # Calculate semantic value
    semantic_score = calculate_semantic_value(
        var_name=assignment.var_name,
        rhs_source=assignment.rhs_source,
        rhs_node=assignment.rhs_node,
        has_type_annotation=assignment.has_type_annotation,
    )

    # Report violations with low semantic value (< 50)
    # Score 50+ indicates the variable adds meaningful clarity
    return semantic_score < 50


def should_autofix(
    lifecycle: VariableLifecycle,
    pattern: PatternType,
) -> bool:
    """Determine if a violation should be auto-fixed (conservative).

    Only auto-fix when:
    1. Pattern is IMMEDIATE_SINGLE_USE or LITERAL_IDENTITY
    2. Semantic score ≤ 20 (very low semantic value)
    3. RHS is literal or simple name/attribute

    Args:
        lifecycle: Variable lifecycle
        pattern: Detected pattern type

    Returns:
        True if should auto-fix
    """
    # Only auto-fix immediate use or literal identity patterns
    if pattern not in {PatternType.IMMEDIATE_SINGLE_USE, PatternType.LITERAL_IDENTITY}:
        return False

    # Calculate semantic value
    assignment = lifecycle.assignment
    semantic_score = calculate_semantic_value(
        var_name=assignment.var_name,
        rhs_source=assignment.rhs_source,
        rhs_node=assignment.rhs_node,
        has_type_annotation=assignment.has_type_annotation,
    )

    # Only auto-fix if semantic value is very low (≤ 20)
    if semantic_score > 20:
        return False

    # Only auto-fix simple RHS expressions
    rhs_node = assignment.rhs_node
    if isinstance(
        rhs_node,
        ast.Constant | ast.Name | ast.Attribute,
    ):
        return True

    # Also allow simple calls (no *args or **kwargs)
    if isinstance(rhs_node, ast.Call):
        # Check if it's a simple call (no varargs)
        if not rhs_node.args and not rhs_node.keywords:
            return True
        # Allow calls with only simple arguments
        if all(isinstance(arg, ast.Constant | ast.Name) for arg in rhs_node.args):
            return True

    return False
