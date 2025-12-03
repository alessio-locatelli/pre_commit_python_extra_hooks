"""Test fixture for linter pragma comments that should NOT be moved."""

# Example 1: flake8/ruff noqa
result = some_very_long_function_name_that_exceeds_line_length()  # noqa: E501

# Example 2: mypy type ignore
value = cast(int, some_object)  # type: ignore

# Example 3: coverage pragma
if DEBUG:  # pragma: no cover
    log_debug_info()

# Example 4: pylint directive
dangerous_eval = eval(user_input)  # pylint: disable=eval-used

# Example 5: mypy specific error
x: int = "string"  # mypy: ignore-errors

# Example 6: pyright directive
y = get_value()  # pyright: ignore

# Example 7: ruff specific
z = long_var_name  # ruff: noqa

# Example 8: bandit nosec
password = input("Enter password: ")  # nosec

# Example 9: isort directive
import sys  # isort: skip

# Example 10: Multiple pragmas on same line (edge case)
data = risky_operation()  # noqa: E501  # type: ignore

# Example 11: pragma with specific error code
result2 = another_function()  # pragma: no cover

# Example 12: Complex pragma
complex_result = process()  # type: ignore[arg-type]
