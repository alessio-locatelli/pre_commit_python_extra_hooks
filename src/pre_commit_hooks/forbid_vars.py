"""Pre-commit hook to forbid meaningless variable names like 'data' and 'result'."""

import argparse
import ast
import io
import re
import sys
import tokenize
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# Regex pattern for inline ignore comments (case-insensitive)
IGNORE_PATTERN = re.compile(
    r"#\s*maintainability:\s*ignore\[meaningless-variable-name\]", re.IGNORECASE
)

# Default forbidden variable names
DEFAULT_FORBIDDEN_NAMES = {"data", "result"}

# Default autofix patterns
DEFAULT_AUTOFIX_PATTERNS = {
    "http": [
        {"regex": r"\.get\(.*\)", "name": "response"},
        {"regex": r"\.post\(.*\)", "name": "response"},
        {"regex": r"\.json\(\)", "name": "payload"},
    ],
    "file": [
        {"regex": r"open\(.*\)", "name": "file_handle"},
        {"regex": r"\.read_text\(.*\)", "name": "file_content"},
        {"regex": r"\.read\(.*\)", "name": "content"},
        {"regex": r"json\.load\(.*\)", "name": "parsed_data"},
    ],
    "database": [
        {"regex": r"\.execute\(.*\)", "name": "cursor"},
        {"regex": r"\.fetchall\(.*\)", "name": "rows"},
        {"regex": r"\.objects\.filter\(.*\)", "name": "queryset"},
        {"regex": r"\.objects\.get\(.*\)", "name": "instance"},
    ],
    "data-science": [
        {"regex": r"pd\.read_csv\(.*\)", "name": "df"},
        {"regex": r"np\.array\(.*\)", "name": "arr"},
        {"regex": r"re\.search\(.*\)", "name": "match"},
        {"regex": r"re\.findall\(.*\)", "name": "matches"},
    ],
    "semantic": [
        {"regex": r"get_([a-zA-Z0-9_]+)\(.*\)", "name": r"\1"},
        {"regex": r"find_([a-zA-Z0-9_]+)\(.*\)", "name": r"found_\1"},
        {"regex": r"create_([a-zA-Z0-9_]+)\(.*\)", "name": r"new_\1"},
    ],
}


def load_autofix_config() -> dict[str, Any]:
    """
    Load autofix configuration from pyproject.toml.

    Returns:
        A dictionary containing the autofix configuration.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {"patterns": DEFAULT_AUTOFIX_PATTERNS, "enabled": ["http"]}

    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    config = pyproject_data.get("tool", {}).get("forbid-vars", {}).get("autofix", {})

    # Combine default and custom patterns
    patterns = DEFAULT_AUTOFIX_PATTERNS.copy()
    custom_patterns = config.get("patterns", [])
    for custom_pattern in custom_patterns:
        category = custom_pattern.get("category")
        if category:
            if category not in patterns:
                patterns[category] = []
            patterns[category].append(
                {
                    "regex": custom_pattern["regex"],
                    "name": custom_pattern["name"],
                }
            )

    # Get enabled categories, default to http
    enabled = config.get("enabled", ["http"])

    return {"patterns": patterns, "enabled": enabled}


class ScopeVisitor(ast.NodeVisitor):
    """A visitor that collects all names in a scope (not nested scopes)."""

    def __init__(self, target_scope: ast.AST | None = None) -> None:
        self.names: set[str] = set()
        self.target_scope = target_scope
        self.in_target_scope = target_scope is None  # Module level = True

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Don't descend into nested function definitions."""
        if node is self.target_scope:
            # This is the target scope - enter it
            self.in_target_scope = True
            self.generic_visit(node)
            self.in_target_scope = False
        elif self.in_target_scope:
            # Nested function - don't descend (separate scope)
            pass
        else:
            # Different scope - don't descend
            pass

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Don't descend into nested async function definitions."""
        if node is self.target_scope:
            # This is the target scope - enter it
            self.in_target_scope = True
            self.generic_visit(node)
            self.in_target_scope = False
        elif self.in_target_scope:
            # Nested function - don't descend (separate scope)
            pass
        else:
            # Different scope - don't descend
            pass

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Don't descend into class definitions (separate scope)."""
        if self.in_target_scope:
            # Class inside function - don't descend
            pass
        else:
            # Continue visiting if we're looking for module-level names
            self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Collect name if we're in the target scope."""
        if self.in_target_scope:
            self.names.add(node.id)
        self.generic_visit(node)


class ForbiddenNameVisitor(ast.NodeVisitor):
    """
    AST visitor that detects forbidden variable names in Python code.

    This visitor checks all contexts where variables are defined and
    tries to find an autofix suggestion.
    """

    def __init__(
        self,
        forbidden_names: set[str],
        source: str,
        autofix_config: dict[str, Any],
        scope_names: set[str],
    ) -> None:
        """
        Initialize the visitor.

        Args:
            forbidden_names: Set of variable names that are not allowed.
            source: The source code of the file being checked.
            autofix_config: Configuration for the autofix feature.
            scope_names: All names defined in the current file's scope.
        """
        self.forbidden_names = forbidden_names
        self.source_lines = source.splitlines()
        self.autofix_config = autofix_config
        self.scope_names = scope_names
        self.violations: list[dict[str, Any]] = []
        # Scope tracking for scope-aware name generation and replacement
        self.current_scope: list[ast.AST] = []
        self.tree: ast.Module | None = None
        self.scope_used_suggestions: dict[int | None, set[str]] = {}
        # Maps (scope_id, forbidden_var_name) to the generated suggestion
        self.scope_var_suggestions: dict[tuple[int | None, str], str] = {}

    def _get_scope_names(self, scope_node: ast.AST | None) -> set[str]:
        """
        Collect all names defined in a specific scope only.

        Args:
            scope_node: The AST node representing the scope (function/class/module).
                       None means module-level scope.

        Returns:
            Set of all variable names defined in that scope.
        """
        visitor = ScopeVisitor(target_scope=scope_node)
        if scope_node:
            visitor.visit(scope_node)
        elif self.tree:
            visitor.visit(self.tree)
        return visitor.names

    def _generate_unique_name(self, suggestion: str, forbidden_var_name: str) -> str:
        """
        Generate a unique variable name considering only the current scope.

        This ensures that variables with the same name in different functions
        don't get unnecessary suffixes (e.g., response_2, response_3).

        Args:
            suggestion: The suggested replacement name
            forbidden_var_name: The original forbidden variable name

        Returns:
            A unique name suitable for this scope
        """
        if suggestion in self.forbidden_names:
            suggestion = "var"  # Fallback

        # Get current scope
        scope_node = self.current_scope[-1] if self.current_scope else None
        scope_id = id(scope_node) if scope_node else None

        # Check if we already generated a suggestion for this variable in this scope
        cache_key = (scope_id, forbidden_var_name)
        if cache_key in self.scope_var_suggestions:
            return self.scope_var_suggestions[cache_key]

        # Get names in THIS scope only (not file-wide!)
        scope_names = self._get_scope_names(scope_node)

        # Track used suggestions in this scope
        if scope_id not in self.scope_used_suggestions:
            self.scope_used_suggestions[scope_id] = set()

        # Check conflicts - only add suffix if there's a conflict in THIS scope
        if (
            suggestion not in scope_names
            and suggestion not in self.scope_used_suggestions[scope_id]
        ):
            self.scope_used_suggestions[scope_id].add(suggestion)
            self.scope_var_suggestions[cache_key] = suggestion
            return suggestion

        # Generate with suffix (only if needed in this scope!)
        counter = 2
        while (
            f"{suggestion}_{counter}" in scope_names
            or f"{suggestion}_{counter}" in self.scope_used_suggestions[scope_id]
        ):
            counter += 1

        unique = f"{suggestion}_{counter}"
        self.scope_used_suggestions[scope_id].add(unique)
        self.scope_var_suggestions[cache_key] = unique
        return unique

    def _find_best_match(self, rhs_source: str) -> dict[str, Any] | None:
        """Find the best autofix pattern for a given RHS source."""
        best_match = None
        max_specificity = -1

        enabled_categories = self.autofix_config.get("enabled", [])
        all_patterns = self.autofix_config.get("patterns", {})

        for category in enabled_categories:
            patterns = all_patterns.get(category, [])
            for pattern in patterns:
                if re.search(pattern["regex"], rhs_source):
                    specificity = len(pattern["regex"])
                    if specificity > max_specificity:
                        max_specificity = specificity
                        best_match = pattern
        return best_match

    def _check_name(
        self,
        name: str,
        lineno: int,
        col_offset: int,
        match: dict[str, Any] | None = None,
    ) -> None:
        """Check if a variable name is forbidden and record violation."""
        if name in self.forbidden_names:
            # Get current scope for scope-aware processing
            scope_node = self.current_scope[-1] if self.current_scope else None

            violation = {
                "name": name,
                "line": lineno,
                "col": col_offset,
                "suggestion": None,
                "scope_id": id(scope_node) if scope_node else None,
                "scope_node": scope_node,
            }
            if match:
                suggested_name = match["name"]
                # Handle semantic naming where name is from regex group
                if "\\" in suggested_name:
                    rhs_source = self.source_lines[lineno - 1]
                    regex_match = re.search(match["regex"], rhs_source)
                    if regex_match:
                        suggested_name = regex_match.expand(suggested_name)

                violation["suggestion"] = self._generate_unique_name(
                    suggested_name, name
                )
            self.violations.append(violation)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit regular assignment nodes: data = 1."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0]
            rhs_source = ast.get_source_segment(
                "".join(f"{line}\n" for line in self.source_lines), node.value
            )
            if rhs_source:
                match = self._find_best_match(rhs_source)
                self._check_name(target.id, target.lineno, target.col_offset, match)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignment nodes: data: int = 1."""
        if isinstance(node.target, ast.Name):
            if node.value:
                rhs_source = ast.get_source_segment(
                    "".join(f"{line}\n" for line in self.source_lines), node.value
                )
                match = self._find_best_match(rhs_source) if rhs_source else None
            else:
                match = None

            self._check_name(
                node.target.id, node.target.lineno, node.target.col_offset, match
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes: def foo(data):."""
        self._check_function_args(node)
        # Push scope before visiting function body
        self.current_scope.append(node)
        self.generic_visit(node)
        # Pop scope after visiting function body
        self.current_scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition nodes: async def foo(data):."""
        self._check_function_args(node)
        # Push scope before visiting function body
        self.current_scope.append(node)
        self.generic_visit(node)
        # Pop scope after visiting function body
        self.current_scope.pop()

    def _check_function_args(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check all function arguments for forbidden names."""
        for arg in node.args.args:
            self._check_name(arg.arg, arg.lineno, arg.col_offset)
        for arg in node.args.posonlyargs:
            self._check_name(arg.arg, arg.lineno, arg.col_offset)
        for arg in node.args.kwonlyargs:
            self._check_name(arg.arg, arg.lineno, arg.col_offset)
        if node.args.vararg:
            self._check_name(
                node.args.vararg.arg,
                node.args.vararg.lineno,
                node.args.vararg.col_offset,
            )
        if node.args.kwarg:
            self._check_name(
                node.args.kwarg.arg, node.args.kwarg.lineno, node.args.kwarg.col_offset
            )


def get_ignored_lines(source: str) -> set[int]:
    """
    Extract line numbers that have inline ignore comments.

    Uses the tokenize module to accurately detect comments (not strings).

    Args:
        source: Python source code as string

    Returns:
        Set of line numbers with ignore comments
    """
    ignored = set()

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)

        for tok_type, tok_string, (line, _), _, _ in tokens:
            if tok_type != tokenize.COMMENT:
                continue

            if IGNORE_PATTERN.search(tok_string):
                ignored.add(line)
    except tokenize.TokenError:
        # If tokenization fails, return empty set (no lines ignored)
        pass

    return ignored


def _get_restricted_positions(source: str) -> set[tuple[int, int]]:
    """Get (line, col) positions where names should NOT be replaced.

    This includes:
    - Function parameter names
    - Keyword argument names
    - Attribute names
    - Any Name node in a string context
    """
    restricted: set[tuple[int, int]] = set()

    try:
        tree = ast.parse(source, filename="<string>")
    except SyntaxError:
        return restricted

    # Collect function parameters
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Function parameters
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if hasattr(arg, "lineno") and hasattr(arg, "col_offset"):
                    restricted.add((arg.lineno, arg.col_offset))
            if node.args.vararg:
                restricted.add((node.args.vararg.lineno, node.args.vararg.col_offset))
            if node.args.kwarg:
                restricted.add((node.args.kwarg.lineno, node.args.kwarg.col_offset))

        # Keyword arguments in function calls
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg:  # Not **kwargs
                    # The keyword name position is roughly the start of the argument
                    # For exact position we'd need more work, so we use a heuristic
                    pass

        # Attribute names
        elif isinstance(node, ast.Attribute):
            # The attr_name's position is after the dot
            if hasattr(node, "lineno") and hasattr(node, "col_offset"):
                # ast doesn't give us exact position of attribute name,
                # but we can estimate it's after the dot in the source
                pass

    return restricted


def _apply_fixes(filepath: str, violations: list[dict[str, Any]], source: str) -> None:
    """
    Apply autofixes by replacing forbidden variable assignments and their uses.

    This implementation is scope-aware: it groups violations by scope and replaces
    ALL uses of a variable within that scope, not just the assignment position.
    This ensures that when 'data' is renamed to 'response', all references to
    'data' in that function are also updated.
    """
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return

    lines = source.splitlines(keepends=True)

    # Step 1: Group violations by scope
    violations_by_scope: dict[int | None, list[dict[str, Any]]] = {}
    for v in violations:
        if v.get("suggestion"):
            scope_id = v.get("scope_id")
            if scope_id not in violations_by_scope:
                violations_by_scope[scope_id] = []
            violations_by_scope[scope_id].append(v)

    if not violations_by_scope:
        return

    # Step 2: Build scope-specific replacement mappings
    scope_replacements: dict[int | None, dict[str, str]] = {}
    for scope_id, scope_violations in violations_by_scope.items():
        replacements: dict[str, str] = {}
        for v in scope_violations:
            old_name = v["name"]
            new_name = v["suggestion"]
            if old_name not in replacements:
                # First violation of this name in this scope wins
                replacements[old_name] = new_name
        scope_replacements[scope_id] = replacements

    # Step 3: Create ScopedNameCollector class
    class ScopedNameCollector(ast.NodeVisitor):
        """Collect Name nodes within a specific scope only (not nested scopes)."""

        def __init__(
            self, scope_node: ast.AST | None, replace_names: dict[str, str]
        ) -> None:
            self.scope_node = scope_node
            self.replace_names = replace_names  # {old_name: new_name}
            self.nodes_to_replace: list[tuple[int, int, str, str]] = []
            self.in_target_scope = scope_node is None  # Module-level = True
            self.param_positions: set[tuple[int, int]] = set()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            """Handle function definitions - enter target scope, skip nested."""
            if node is self.scope_node:
                # Enter target scope
                self.in_target_scope = True
                # Mark parameters as restricted (don't replace parameter names)
                all_args = node.args.args + node.args.posonlyargs + node.args.kwonlyargs
                for arg in all_args:
                    if arg.arg in self.replace_names:
                        self.param_positions.add((arg.lineno, arg.col_offset))
                if node.args.vararg and node.args.vararg.arg in self.replace_names:
                    pos = (node.args.vararg.lineno, node.args.vararg.col_offset)
                    self.param_positions.add(pos)
                if node.args.kwarg and node.args.kwarg.arg in self.replace_names:
                    pos = (node.args.kwarg.lineno, node.args.kwarg.col_offset)
                    self.param_positions.add(pos)
                self.generic_visit(node)
                self.in_target_scope = False
            elif self.in_target_scope:
                # Nested function - don't descend (separate scope)
                pass
            else:
                # Different scope - don't descend
                pass

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            """Handle async function definitions - same logic as visit_FunctionDef."""
            if node is self.scope_node:
                self.in_target_scope = True
                all_args = node.args.args + node.args.posonlyargs + node.args.kwonlyargs
                for arg in all_args:
                    if arg.arg in self.replace_names:
                        self.param_positions.add((arg.lineno, arg.col_offset))
                if node.args.vararg and node.args.vararg.arg in self.replace_names:
                    pos = (node.args.vararg.lineno, node.args.vararg.col_offset)
                    self.param_positions.add(pos)
                if node.args.kwarg and node.args.kwarg.arg in self.replace_names:
                    pos = (node.args.kwarg.lineno, node.args.kwarg.col_offset)
                    self.param_positions.add(pos)
                self.generic_visit(node)
                self.in_target_scope = False
            elif self.in_target_scope:
                pass
            else:
                pass

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            """Don't descend into class definitions (separate scope)."""
            if self.in_target_scope:
                # Class inside function - don't descend
                pass
            else:
                # Continue visiting if we're looking for module-level names
                self.generic_visit(node)

        def visit_Name(self, node: ast.Name) -> None:
            """Collect Name node if we're in the target scope."""
            if self.in_target_scope and node.id in self.replace_names:
                pos = (node.lineno, node.col_offset)
                if pos not in self.param_positions:
                    replacement = (
                        node.lineno,
                        node.col_offset,
                        node.id,
                        self.replace_names[node.id],
                    )
                    self.nodes_to_replace.append(replacement)
            self.generic_visit(node)

    # Step 4: Collect replacements for each scope
    all_replacements: list[tuple[int, int, str, str]] = []
    for scope_id, replacements in scope_replacements.items():
        # Find scope node from first violation
        scope_node = None
        for v in violations_by_scope[scope_id]:
            scope_node = v.get("scope_node")
            break

        # Collect Name nodes in this scope
        collector = ScopedNameCollector(scope_node, replacements)
        if scope_node:
            collector.visit(scope_node)
        else:
            collector.visit(tree)
        all_replacements.extend(collector.nodes_to_replace)

    # Step 5: Sort reverse and apply replacements
    all_replacements.sort(key=lambda x: (x[0], x[1]), reverse=True)

    for line_num, col, old_name, new_name in all_replacements:
        line_idx = line_num - 1
        if line_idx >= len(lines):
            continue

        line = lines[line_idx]
        name_len = len(old_name)

        # Bounds check
        if col >= len(line) or col + name_len > len(line):
            continue

        # Verify the name matches at this position
        if line[col : col + name_len] != old_name:
            continue

        # Check word boundaries
        before_ok = col == 0 or not (line[col - 1].isalnum() or line[col - 1] == "_")
        after_ok = col + name_len >= len(line) or not (
            line[col + name_len].isalnum() or line[col + name_len] == "_"
        )

        if before_ok and after_ok:
            lines[line_idx] = line[:col] + new_name + line[col + name_len :]

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)


def check_file(
    filepath: str,
    forbidden_names: set[str],
    fix: bool = False,
    autofix_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Check a Python file for forbidden variable names.

    Args:
        filepath: Path to the Python file to check
        forbidden_names: Set of forbidden variable names
        fix: If True, automatically fix violations when possible
        autofix_config: Configuration for the autofix feature

    Returns:
        List of violations.
    """
    if autofix_config is None:
        autofix_config = {}
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    ignored_lines = get_ignored_lines(source)

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    scope_visitor = ScopeVisitor()
    scope_visitor.visit(tree)
    scope_names = scope_visitor.names

    visitor = ForbiddenNameVisitor(forbidden_names, source, autofix_config, scope_names)
    visitor.tree = tree  # Store tree for scope-aware name generation
    visitor.visit(tree)

    violations = [v for v in visitor.violations if v["line"] not in ignored_lines]

    if fix:
        fixable_violations = [v for v in violations if v.get("suggestion")]
        if fixable_violations:
            _apply_fixes(filepath, fixable_violations, source)
            for v in violations:
                if v in fixable_violations:
                    v["fixed"] = True

    return violations


def report_violation(
    filepath: str, line: int, name: str, suggestion: str | None = None
) -> None:
    """



    Report a single violation with helpful message and link.







    Follows standard linter format: filepath:line: message







    Args:



        filepath: Path to the file containing the violation



        line: Line number where the violation occurs



        name: The forbidden variable name found



        suggestion: The suggested new name, if any



    """

    message = f"Forbidden variable name '{name}' found."

    if suggestion:
        message += f" Consider renaming to '{suggestion}'."

    else:
        message += " Use a more descriptive name."

    message += (
        " Or add '# maintainability: ignore[meaningless-variable-name]' to suppress. "
        "See https://hilton.org.uk/blog/meaningless-variable-names"
    )

    print(f"{filepath}:{line}: {message}")


def report_fix(filepath: str, line: int, name: str, suggestion: str) -> None:
    """Report a successfully applied fix."""

    print(f"Applied fix for '{name}' -> '{suggestion}' in {filepath}:{line}")


def main(argv: Sequence[str] | None = None) -> int:
    """











    Main entry point for the forbid-vars hook.























    Args:











        argv: Command-line arguments (defaults to sys.argv if None)























    Returns:











        Exit code: 0 for success, 1 for failure











    """

    parser = argparse.ArgumentParser(
        description="Check for forbidden variable names in Python files"
    )

    parser.add_argument("filenames", nargs="*", help="Filenames to check")

    parser.add_argument(
        "--names",
        default="data,result",
        help="Comma-separated list of forbidden names (default: data,result)",
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix forbidden names where possible.",
    )

    args = parser.parse_args(argv)

    # Load autofix configuration

    autofix_config = load_autofix_config()

    # Parse forbidden names from argument

    forbidden_names = {n.strip() for n in args.names.split(",") if n.strip()}

    if not forbidden_names:
        # If no forbidden names provided, exit successfully

        return 0

    # Check all files

    failed = False

    for filepath in args.filenames:
        violations = check_file(filepath, forbidden_names, args.fix, autofix_config)

        if violations:
            failed = True

            for v in violations:
                if v.get("fixed"):
                    report_fix(filepath, v["line"], v["name"], v["suggestion"])

                else:
                    report_violation(
                        filepath, v["line"], v["name"], v.get("suggestion")
                    )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
