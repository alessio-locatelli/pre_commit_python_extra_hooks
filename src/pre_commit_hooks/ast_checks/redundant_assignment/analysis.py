"""Variable tracking and redundancy pattern detection for TRI005."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class PatternType(Enum):
    """Types of redundant assignment patterns."""

    IMMEDIATE_SINGLE_USE = auto()  # x = "foo"; func(x=x)
    SINGLE_USE = auto()  # x = calc(); return x
    LITERAL_IDENTITY = auto()  # foo = "foo"


@dataclass
class AssignmentInfo:
    """Tracks a variable assignment.

    Attributes:
        var_name: Variable name
        line: Line number of assignment
        col: Column offset of assignment
        stmt_index: Position in scope body (for distance calculation)
        rhs_node: Right-hand side AST node
        rhs_source: Right-hand side source code
        scope_id: Scope identifier for isolation
        has_type_annotation: Whether assignment has type annotation
    """

    var_name: str
    line: int
    col: int
    stmt_index: int
    rhs_node: ast.expr
    rhs_source: str
    scope_id: int
    has_type_annotation: bool = False


@dataclass
class UsageInfo:
    """Tracks a variable usage.

    Attributes:
        var_name: Variable name
        line: Line number of usage
        col: Column offset of usage
        stmt_index: Position in scope body
        context: Usage context ('return', 'call', 'operation', etc.)
        scope_id: Scope identifier for isolation
    """

    var_name: str
    line: int
    col: int
    stmt_index: int
    context: str
    scope_id: int


@dataclass
class VariableLifecycle:
    """Complete lifecycle of a variable in its scope.

    Attributes:
        assignment: Assignment information
        uses: List of all uses of the variable
    """

    assignment: AssignmentInfo
    uses: list[UsageInfo]

    @property
    def is_single_use(self) -> bool:
        """Check if variable is used exactly once."""
        return len(self.uses) == 1

    @property
    def is_immediate_use(self) -> bool:
        """Check if first use is within 0-1 statements from assignment."""
        if not self.uses:
            return False
        first_use = self.uses[0]
        # Immediate = same statement or next statement
        return first_use.stmt_index <= self.assignment.stmt_index + 1


class VariableTracker(ast.NodeVisitor):
    """Tracks variable assignments and uses across scopes.

    This visitor traverses the AST and builds a comprehensive map of variable
    lifecycles, tracking where variables are assigned and where they're used.
    """

    def __init__(self, source: str):
        """Initialize the tracker.

        Args:
            source: Source code being analyzed
        """
        self.source = source
        self.source_lines = source.splitlines()

        # Scope tracking
        self.current_scope_id = 0
        self.scope_stack: list[int] = [0]  # Start with module scope

        # Statement index tracking within current scope
        self.stmt_index_stack: list[int] = [0]

        # Track assignments: (scope_id, var_name) -> list[AssignmentInfo]
        self.assignments: dict[tuple[int, str], list[AssignmentInfo]] = {}

        # Track uses: (scope_id, var_name) -> list[UsageInfo]
        self.uses: dict[tuple[int, str], list[UsageInfo]] = {}

        # Track global/nonlocal declarations to skip them
        self.global_vars: set[tuple[int, str]] = set()
        self.nonlocal_vars: set[tuple[int, str]] = set()

        # Track which names are currently being assigned (to avoid treating
        # the LHS of an assignment as a use)
        self.currently_assigning: set[str] = set()

    def _enter_scope(self) -> None:
        """Enter a new scope (function, class, etc.)."""
        self.current_scope_id += 1
        self.scope_stack.append(self.current_scope_id)
        self.stmt_index_stack.append(0)

    def _exit_scope(self) -> None:
        """Exit the current scope."""
        self.scope_stack.pop()
        self.stmt_index_stack.pop()

    def _increment_stmt_index(self) -> None:
        """Increment the statement index in the current scope."""
        # Defensive guard: stack initialized with [0] in __init__ and maintained
        # via balanced _enter_scope/_exit_scope calls; should never be empty
        if self.stmt_index_stack:  # pragma: lax no cover
            self.stmt_index_stack[-1] += 1

    def _get_current_scope_id(self) -> int:
        """Get the current scope ID."""
        return self.scope_stack[-1] if self.scope_stack else 0

    def _get_current_stmt_index(self) -> int:
        """Get the current statement index."""
        return self.stmt_index_stack[-1] if self.stmt_index_stack else 0

    def _get_source_segment(self, node: ast.expr) -> str:
        """Get source code for an AST node.

        Args:
            node: AST node

        Returns:
            Source code string, or empty string if unavailable
        """
        try:
            return ast.get_source_segment(self.source, node) or ""
        except (ValueError, TypeError):  # pragma: no cover
            return ""

    def _is_simple_name_target(self, target: ast.expr) -> bool:
        """Check if assignment target is a simple name (not tuple, attribute, etc.).

        Args:
            target: Assignment target node

        Returns:
            True if target is a simple name
        """
        return isinstance(target, ast.Name)

    def visit_Global(self, node: ast.Global) -> None:
        """Track global declarations."""
        scope_id = self._get_current_scope_id()
        for name in node.names:
            self.global_vars.add((scope_id, name))
        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        """Track nonlocal declarations."""
        scope_id = self._get_current_scope_id()
        for name in node.names:
            self.nonlocal_vars.add((scope_id, name))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Visit function definition (enter new scope).

        Args:
            node: Function definition node
        """
        self._enter_scope()

        # Visit function body
        for stmt in node.body:
            self.visit(stmt)
            self._increment_stmt_index()

        self._exit_scope()

    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition (enter new scope).

        We skip class-level assignments as they're attributes, not local variables.

        Args:
            node: Class definition node
        """
        self._enter_scope()

        # Visit class body but don't track assignments at class level
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                self.visit(stmt)
            # Skip direct assignments in class body (class attributes)

        self._exit_scope()

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track simple assignments.

        Args:
            node: Assignment node
        """
        scope_id = self._get_current_scope_id()
        stmt_index = self._get_current_stmt_index()

        # Only track simple name assignments (not tuple unpacking, attributes, etc.)
        for target in node.targets:
            if self._is_simple_name_target(target):
                assert isinstance(target, ast.Name)  # Type narrowing
                var_name = target.id

                # Skip global/nonlocal variables
                if (scope_id, var_name) in self.global_vars | self.nonlocal_vars:
                    continue

                # Mark as currently assigning to avoid treating LHS as use
                self.currently_assigning.add(var_name)

                # Get RHS source
                rhs_source = self._get_source_segment(node.value)

                # Create assignment info
                assignment = AssignmentInfo(
                    var_name=var_name,
                    line=node.lineno,
                    col=node.col_offset,
                    stmt_index=stmt_index,
                    rhs_node=node.value,
                    rhs_source=rhs_source,
                    scope_id=scope_id,
                    has_type_annotation=False,
                )

                # Store assignment
                key = (scope_id, var_name)
                if key not in self.assignments:
                    self.assignments[key] = []
                self.assignments[key].append(assignment)

        # Visit RHS to track any variable uses
        self.visit(node.value)

        # Clear currently assigning
        self.currently_assigning.clear()

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Track annotated assignments.

        Args:
            node: Annotated assignment node
        """
        scope_id = self._get_current_scope_id()
        stmt_index = self._get_current_stmt_index()

        # Only track simple name assignments
        if self._is_simple_name_target(node.target) and node.value is not None:
            assert isinstance(node.target, ast.Name)  # Type narrowing
            var_name = node.target.id

            # Skip global/nonlocal variables
            if (scope_id, var_name) in self.global_vars | self.nonlocal_vars:
                return

            # Mark as currently assigning
            self.currently_assigning.add(var_name)

            # Get RHS source
            rhs_source = self._get_source_segment(node.value)

            # Create assignment info
            assignment = AssignmentInfo(
                var_name=var_name,
                line=node.lineno,
                col=node.col_offset,
                stmt_index=stmt_index,
                rhs_node=node.value,
                rhs_source=rhs_source,
                scope_id=scope_id,
                has_type_annotation=True,  # This is an annotated assignment
            )

            # Store assignment
            key = (scope_id, var_name)
            if key not in self.assignments:
                self.assignments[key] = []
            self.assignments[key].append(assignment)

            # Visit RHS
            self.visit(node.value)

            # Clear currently assigning
            self.currently_assigning.clear()

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Track augmented assignments (+=, -=, etc.).

        Augmented assignments READ the variable (to get current value) and then
        mutate it in place. We track the READ as a usage, which prevents false
        positives for patterns like:
            if condition:
                msg = "foo"
            else:
                msg = "bar"
            msg += " suffix"  # This USES the conditional value

        We don't track augmented assignments as NEW assignments because they're
        mutations of existing variables, not fresh assignments that could be
        inlined.

        Args:
            node: Augmented assignment node
        """
        scope_id = self._get_current_scope_id()
        stmt_index = self._get_current_stmt_index()

        # Only track simple name targets
        if self._is_simple_name_target(node.target):
            assert isinstance(node.target, ast.Name)  # Type narrowing
            var_name = node.target.id

            # Skip global/nonlocal variables
            if (scope_id, var_name) in self.global_vars | self.nonlocal_vars:
                self.generic_visit(node)
                return

            # Track the READ (use) of the current value
            usage = UsageInfo(
                var_name=var_name,
                line=node.lineno,
                col=node.col_offset,
                stmt_index=stmt_index,
                context="augmented_assignment",
                scope_id=scope_id,
            )
            key = (scope_id, var_name)
            if key not in self.uses:  # pragma: lax no cover
                self.uses[key] = []
            self.uses[key].append(usage)

        # Visit RHS to track any uses of other variables
        self.visit(node.value)

    def visit_Name(self, node: ast.Name) -> None:
        """Track variable uses (loads).

        Args:
            node: Name node
        """
        # Only track loads (uses), not stores (assignments)
        if not isinstance(node.ctx, ast.Load):
            return

        # Skip if we're currently assigning to this variable
        # (to avoid treating LHS as a use in `x = x + 1`)
        if node.id in self.currently_assigning:
            return

        scope_id = self._get_current_scope_id()
        stmt_index = self._get_current_stmt_index()

        # Determine context
        context = "unknown"
        # Walk up parent nodes to determine context
        # (This is a simplified version - a full implementation would use
        # a parent tracking system)

        # Create usage info
        usage = UsageInfo(
            var_name=node.id,
            line=node.lineno,
            col=node.col_offset,
            stmt_index=stmt_index,
            context=context,
            scope_id=scope_id,
        )

        # Store usage
        key = (scope_id, node.id)
        if key not in self.uses:
            self.uses[key] = []
        self.uses[key].append(usage)

        self.generic_visit(node)

    def build_lifecycles(self) -> list[VariableLifecycle]:
        """Build variable lifecycles from tracked assignments and uses.

        Returns:
            List of variable lifecycles
        """
        lifecycles: list[VariableLifecycle] = []

        # For each assignment, find its corresponding uses
        for (scope_id, var_name), assignment_list in self.assignments.items():
            # For each assignment to this variable
            for assignment in assignment_list:
                # Find uses of this variable in the same scope after this assignment
                key = (scope_id, var_name)
                all_uses = self.uses.get(key, [])

                # Filter uses that come after this assignment
                # (by comparing statement indices)
                relevant_uses = [
                    use for use in all_uses if use.stmt_index >= assignment.stmt_index
                ]

                # If there's a subsequent assignment to the same variable,
                # only include uses up to that assignment
                next_assignment = None
                for other_assignment in assignment_list:
                    if other_assignment.stmt_index > assignment.stmt_index and (
                        next_assignment is None
                        or other_assignment.stmt_index < next_assignment.stmt_index
                    ):
                        next_assignment = other_assignment

                if next_assignment:
                    # Only include uses before the next assignment
                    relevant_uses = [
                        use
                        for use in relevant_uses
                        if use.stmt_index < next_assignment.stmt_index
                    ]

                # Create lifecycle
                lifecycle = VariableLifecycle(
                    assignment=assignment,
                    uses=relevant_uses,
                )
                lifecycles.append(lifecycle)

        return lifecycles


def detect_redundancy(lifecycle: VariableLifecycle) -> PatternType | None:
    """Detect if a variable lifecycle represents a redundant assignment.

    Args:
        lifecycle: Variable lifecycle to analyze

    Returns:
        Pattern type if redundant, None otherwise
    """
    # Must be single use
    if not lifecycle.is_single_use:
        return None

    # Pattern 3: Literal identity (e.g., foo = "foo")
    if _is_literal_identity(lifecycle):
        return PatternType.LITERAL_IDENTITY

    # Pattern 1: Immediate single use
    if lifecycle.is_immediate_use:
        return PatternType.IMMEDIATE_SINGLE_USE

    # Pattern 2: Single use anywhere
    return PatternType.SINGLE_USE


def _is_literal_identity(lifecycle: VariableLifecycle) -> bool:
    """Check if assignment is a literal identity (e.g., foo = "foo").

    Args:
        lifecycle: Variable lifecycle to check

    Returns:
        True if literal identity
    """
    assignment = lifecycle.assignment
    rhs_node = assignment.rhs_node

    # Check if RHS is a string literal
    if isinstance(rhs_node, ast.Constant) and isinstance(rhs_node.value, str):
        # Check if variable name matches literal value (case-insensitive)
        var_name = assignment.var_name.lower()
        literal_value = rhs_node.value.lower()

        # Direct match or variable name matches literal
        if var_name == literal_value:
            return True

        # Also check if variable name is literal with case changes
        # (e.g., FOO = "foo")
        if var_name.replace("_", "") == literal_value.replace("_", ""):
            return True

    return False


def process_file(filepath: Path) -> list[VariableLifecycle]:
    """Process a file and return all variable lifecycles.

    Args:
        filepath: Path to Python file

    Returns:
        List of variable lifecycles, or empty list if file cannot be parsed
    """
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    tracker = VariableTracker(source)
    tracker.visit(tree)
    return tracker.build_lifecycles()
