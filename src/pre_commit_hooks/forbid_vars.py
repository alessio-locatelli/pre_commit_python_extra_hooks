"""Pre-commit hook to forbid meaningless variable names like 'data' and 'result'."""

import argparse
import ast
import io
import re
import sys
import tokenize
from pathlib import Path
from typing import Any, Sequence

try:
    import tomllib
except ImportError:
    # Python < 3.11
    import toml as tomllib

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
    """A visitor that collects all names in a scope."""

    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
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

    def _generate_unique_name(self, suggestion: str) -> str:
        """Generate a unique variable name if the suggestion already exists."""
        if suggestion in self.forbidden_names:
            suggestion = "var"  # Fallback

        new_name = suggestion
        counter = 2
        while new_name in self.scope_names:
            new_name = f"{suggestion}_{counter}"
            counter += 1
        return new_name

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
        self, name: str, lineno: int, col_offset: int, match: dict[str, Any] | None = None
    ) -> None:
        """Check if a variable name is forbidden and record violation."""
        if name in self.forbidden_names:
            violation = {
                "name": name,
                "line": lineno,
                "col": col_offset,
                "suggestion": None,
            }
            if match:
                suggested_name = match["name"]
                # Handle semantic naming where name is from regex group
                if "\\" in suggested_name:
                    rhs_source = self.source_lines[lineno - 1]
                    regex_match = re.search(match["regex"], rhs_source)
                    if regex_match:
                        suggested_name = regex_match.expand(suggested_name)

                violation["suggestion"] = self._generate_unique_name(suggested_name)
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

            self._check_name(node.target.id, node.target.lineno, node.target.col_offset, match)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes: def foo(data):."""
        self._check_function_args(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition nodes: async def foo(data):."""
        self._check_function_args(node)
        self.generic_visit(node)

    def _check_function_args(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
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


def _apply_fixes(filepath: str, violations: list[dict[str, Any]], source: str) -> None:
    """Apply autofixes to a file by simple search and replace."""
    # This is a simple implementation that doesn't respect scopes,
    # but it's good enough for this hook's purpose.
    source_to_modify = source

    # Create a unique set of replacements to perform
    replacements = {}
    for v in violations:
        if v["suggestion"]:
            replacements[v["name"]] = v["suggestion"]

    for old_name, new_name in replacements.items():
        source_to_modify = re.sub(r"\b" + re.escape(old_name) + r"\b", new_name, source_to_modify)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(source_to_modify)


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


def report_violation(filepath: str, line: int, name: str, suggestion: str | None = None) -> None:
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
                    report_violation(filepath, v["line"], v["name"], v.get("suggestion"))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
