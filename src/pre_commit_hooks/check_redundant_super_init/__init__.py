"""Detect redundant **kwargs forwarding to parent __init__ methods.

MAINTAINABILITY-006: Detects when a class forwards **kwargs to a parent
__init__ that accepts no arguments. This is a logic error that creates
misleading inheritance patterns.

Example:
    Bad:  class Child(Parent):
              def __init__(self, **kwargs):
                  super().__init__(**kwargs)  # Parent.__init__ has no params

    Good: class Child(Parent):
              def __init__(self):
                  super().__init__()
"""

import argparse
import ast
import sys
from pathlib import Path

from pre_commit_hooks._cache import CacheManager
from pre_commit_hooks._prefilter import git_grep_filter


class SuperInitChecker(ast.NodeVisitor):
    """AST visitor to check for redundant super().__init__(**kwargs)."""

    def __init__(self, filename: str):
        """Initialize checker.

        Args:
            filename: Name of file being checked
        """
        self.filename = filename
        self.violations: list[tuple[int, str]] = []
        self.classes: dict[str, ast.ClassDef] = {}  # Track class definitions

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition.

        Args:
            node: ClassDef AST node
        """
        # Store class for later lookup
        self.classes[node.name] = node

        # Find __init__ method
        init_method = None
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                init_method = item
                break

        if init_method:
            self._check_init_method(node, init_method)

        # Continue visiting child nodes
        self.generic_visit(node)

    def _check_init_method(
        self, class_node: ast.ClassDef, init_node: ast.FunctionDef
    ) -> None:
        """Check if __init__ forwards kwargs to parent that doesn't accept them.

        Args:
            class_node: The class definition
            init_node: The __init__ method
        """
        # Check if __init__ has **kwargs parameter
        has_kwargs = init_node.args.kwarg is not None
        if not has_kwargs:
            return

        # Find super().__init__() calls in the __init__ method
        for stmt in ast.walk(init_node):
            if not isinstance(stmt, ast.Call):
                continue

            # Check if this is super().__init__() call
            if not self._is_super_init_call(stmt):
                continue

            # Check if **kwargs is forwarded
            if not self._forwards_kwargs(stmt):
                continue

            # Check parent signatures
            for base in class_node.bases:
                if isinstance(base, ast.Name):
                    parent = self.classes.get(base.id)
                    if parent and not self._parent_accepts_args(parent, self.classes):
                        self.violations.append(
                            (
                                init_node.lineno,
                                f"Redundant **kwargs forwarded to {base.id}.__init__() "
                                f"which accepts no arguments",
                            )
                        )

    @staticmethod
    def _is_super_init_call(node: ast.Call) -> bool:
        """Check if node is a super().__init__() call.

        Args:
            node: Call AST node

        Returns:
            True if this is super().__init__()
        """
        # Check if func is Attribute with value=Call(super) and attr='__init__'
        if not isinstance(node.func, ast.Attribute):
            return False

        if node.func.attr != "__init__":
            return False

        # Check if the value is a super() call
        if not isinstance(node.func.value, ast.Call):
            return False

        func = node.func.value.func
        return isinstance(func, ast.Name) and func.id == "super"

    @staticmethod
    def _forwards_kwargs(node: ast.Call) -> bool:
        """Check if call forwards **kwargs.

        Args:
            node: Call AST node

        Returns:
            True if **kwargs is forwarded
        """
        # Check keywords for **kwargs (Starred node)
        return any(keyword.arg is None for keyword in node.keywords)

    @staticmethod
    def _parent_accepts_args(
        class_node: ast.ClassDef, classes: dict[str, ast.ClassDef]
    ) -> bool:
        """Check if parent's __init__ accepts any arguments.

        This method recursively traverses the inheritance chain to determine
        if any ancestor class accepts arguments through its __init__ method.

        Args:
            class_node: The parent class definition
            classes: Dictionary mapping class names to their AST nodes

        Returns:
            True if __init__ accepts arguments beyond self
        """
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                # Check if it has any parameters beyond 'self'
                args = item.args
                # Check positional arguments beyond 'self'
                if len(args.args) > 1:
                    return True
                # Check for *args or **kwargs
                if args.vararg or args.kwarg:
                    return True
                # Check for keyword-only arguments (e.g., *, key=None)
                if args.kwonlyargs:
                    return True
                # Check for positional-only args (e.g., /, value)
                # Exclude 'self', so check for more than 1 posonly arg
                return bool(args.posonlyargs and len(args.posonlyargs) > 1)

        # No __init__ defined, recursively check parent classes
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                # For built-in or imported types, we can't check further
                # but Exception and its subclasses accept **kwargs through BaseException
                if base.id in ("Exception", "BaseException"):
                    return True
                # Recursively check user-defined parent classes
                parent = classes.get(base.id)
                if parent and SuperInitChecker._parent_accepts_args(parent, classes):
                    return True
        return False


def check_file(filename: str) -> list[tuple[int, str]]:
    """Check file for redundant super init kwargs.

    Args:
        filename: Path to Python file

    Returns:
        List of (line_number, message) tuples
    """
    try:
        with open(filename, encoding="utf-8") as f:
            source = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source, filename)
    except SyntaxError:
        return []

    checker = SuperInitChecker(filename)
    checker.visit(tree)
    return checker.violations


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 if no violations, 1 if violations found)
    """
    parser = argparse.ArgumentParser(
        description="Check for redundant super init kwargs forwarding"
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check")

    args = parser.parse_args(argv)

    if not args.filenames:
        return 0

    # Pre-filter: only process files with super().__init__ calls
    candidates = git_grep_filter(args.filenames, "super().__init__", fixed_string=True)
    # All test fixtures contain super().__init__ pattern, so this early
    # exit never triggers in tests; works in real usage
    if not candidates:  # pragma: no cover
        return 0

    # Initialize cache
    cache = CacheManager(hook_name="check-redundant-super-init")

    exit_code = 0
    for filename in candidates:
        filepath = Path(filename)

        # Try cache first
        cached = cache.get_cached_result(filepath, "check-redundant-super-init")
        # Tests run with cold cache to verify analysis logic; warm cache
        # path is exercised in benchmarks and real usage
        if cached is not None:  # pragma: no cover
            violations = [tuple(v) for v in cached.get("violations", [])]
        else:
            violations = check_file(filename)
            cache.set_cached_result(
                filepath,
                "check-redundant-super-init",
                {"violations": [list(v) for v in violations]},
            )

        for line_num, message in violations:
            print(
                f"{filename}:{line_num}: MAINTAINABILITY-006: {message}",
                file=sys.stderr,
            )
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
