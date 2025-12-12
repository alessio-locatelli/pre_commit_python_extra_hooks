"""Function name suggestion logic."""

from __future__ import annotations

import ast

from .analysis import GET_PREFIX, is_decorator_override_or_abstract


def derive_entity_from_name(func_name: str) -> str:
    """Extract entity name by removing get_ prefix.

    Args:
        func_name: Function name (e.g., "get_users")

    Returns:
        Entity name without prefix (e.g., "users")
    """
    if func_name.startswith(GET_PREFIX):
        return func_name[len(GET_PREFIX) :]
    return func_name


def first_docstring_line(func_node: ast.FunctionDef) -> str | None:
    """Extract first line of function docstring.

    Args:
        func_node: Function AST node

    Returns:
        First line of docstring, or None if no docstring
    """
    if (
        func_node.body
        and isinstance(func_node.body[0], ast.Expr)
        and isinstance(func_node.body[0].value, (ast.Constant,))
        and isinstance(func_node.body[0].value.value, str)
    ):
        s = func_node.body[0].value.value.strip()
        return s.splitlines()[0].strip() if s else None
    return None


def suggest_name_for(
    func_node: ast.FunctionDef, analysis: dict[str, bool]
) -> tuple[str, str]:
    """Suggest a better name for a function based on behavioral analysis.

    Args:
        func_node: The function AST node
        analysis: Dictionary of detected behaviors from analyze_function()

    Returns:
        Tuple of (suggested_name, reason)

    Suggestion priority (first match wins):
    1. Properties → noun
    2. Collection/parsing → extract_/parse_
    3. Searching → find_
    4. I/O operations → load_/save_to_/fetch_
    5. Boolean → is_
    6. Aggregation → calculate_
    7. Generator → iter_
    8. Creation → create_
    9. Mutation → update_
    10. Validation → validate_
    11. Rendering → render_
    12. Transformation → transform_
    Fallback: "no confident suggestion"
    """
    old = func_node.name
    entity = derive_entity_from_name(old)

    # Tests: if name starts with test_ -> do not touch
    if old.startswith("test_"):
        return old, "function looks like a test"

    # Skip abstract/override decorated functions
    if is_decorator_override_or_abstract(func_node):
        return old, "skip: decorated with @override or @abstractmethod"

    # If function appears to just delegate to another get_* call
    # and return that result, skip suggestion
    if analysis["delegates_get"]:
        return old, "delegates to another get_ function; skipping suggestion"

    # docstring heuristic: 'Get or create'
    first_line = first_docstring_line(func_node)
    if first_line:
        low = first_line.lower()
        if low.startswith("get or create") or "get or create" in low:
            suggested = f"get_or_create_{entity}" if entity else "get_or_create"
            return suggested, "docstring: 'get or create'"

    if analysis["is_property"]:
        suggested = entity or old
        reason = "@property: prefer noun name rather than verb"
        return suggested, reason

    # collection/parsing/extraction (prefer these before create/update)
    if analysis["collects"]:
        # if parsing was detected (json.loads etc.), prefer parse_ otherwise extract_
        if analysis["parses"]:
            suggested = f"parse_{entity}" if entity else "parse"
            reason = "parses/collects structured data from a source"
            return suggested, reason
        suggested = f"extract_{entity}" if entity else "extract"
        reason = "extracts/collects data (returns list/dict)"
        return suggested, reason

    if analysis["parses"]:
        suggested = f"parse_{entity}" if entity else "parse"
        reason = "parses input (json/yaml/...)"
        return suggested, reason

    # searches/finding patterns (e.g., find_root)
    if analysis["searches"]:
        suggested = f"find_{entity}" if entity else "find"
        reason = "searches or finds an item (filesystem or structure)"
        return suggested, reason

    # disk/network priority
    if analysis["disk_write"] or analysis["network_write"]:
        verb = "save_to" if analysis["disk_write"] else "send"
        suggested = f"{verb}_{entity}" if entity else f"{verb}"
        reason = "persists or sends data (write)"
        return suggested, reason

    if analysis["network_read"]:
        suggested = f"fetch_{entity}" if entity else "fetch"
        reason = "fetches data over network"
        return suggested, reason

    if analysis["disk_read"]:
        suggested = f"load_{entity}" if entity else "load"
        reason = "reads data from disk"
        return suggested, reason

    if analysis["outputs"]:
        suggested = f"print_{entity}" if entity else "print"
        reason = "outputs data to stdout/log"
        return suggested, reason

    if analysis["returns_bool"]:
        suggested = f"is_{entity}" if entity else f"is_{old}"
        reason = "returns a boolean (annotation)"
        return suggested, reason

    if analysis["aggregates"]:
        suggested = f"calculate_{entity}" if entity else "calculate"
        reason = "aggregates or computes a summary"
        return suggested, reason

    if analysis["yields"]:
        suggested = f"iter_{entity}" if entity else "iter"
        reason = "generator/iterator"
        return suggested, reason

    if analysis["creates_object"]:
        suggested = f"create_{entity}" if entity else "create"
        reason = "creates an object"
        return suggested, reason

    if analysis["mutates_args"]:
        suggested = f"update_{entity}" if entity else f"update_{old}"
        reason = "mutates arguments or state"
        return suggested, reason

    if analysis["validates"]:
        suggested = f"validate_{entity}" if entity else f"validate_{old}"
        reason = "performs validation and returns errors"
        return suggested, reason

    if analysis["renders"]:
        suggested = f"render_{entity}" if entity else "render"
        reason = "renders/serializes data to string"
        return suggested, reason

    if analysis["transforms"]:
        suggested = f"transform_{entity}" if entity else "transform"
        reason = "performs a transformation"
        return suggested, reason

    # fallback: no confident suggestion
    return old, "no confident suggestion"
