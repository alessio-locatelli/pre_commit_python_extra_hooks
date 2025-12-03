"""Module with inheritance chain where only deepest ancestor accepts kwargs.

This is the aiohttp-style pattern where intermediate classes don't define
__init__, but the deepest ancestor does accept **kwargs. The child class
correctly forwards **kwargs, so this should NOT be flagged as an error.
"""


class HTTPException(Exception):
    """Base HTTP exception."""

    pass


class HTTPError(HTTPException):
    """HTTP error exception."""

    pass


class HTTPClientError(HTTPError):
    """HTTP client error (4xx)."""

    pass


class HTTPRequestEntityTooLarge(HTTPClientError):
    """HTTP 413 - Request Entity Too Large.

    This class doesn't define __init__, relying on parent classes.
    The deepest ancestor (HTTPException) implicitly accepts **kwargs
    through Exception.__init__.
    """

    code = 413
    message = "Request Entity Too Large"

    def __init__(self, **kwargs):
        """Initialize with kwargs."""
        super().__init__(**kwargs)
