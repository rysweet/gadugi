"""Type stubs for error_handling module."""

from typing import Any, Optional

class GadugiError(Exception):
    """Base error for Gadugi operations."""
    def __init__(
        self, message: str, details: Optional[dict[str, Any]] = None
    ) -> None: ...
