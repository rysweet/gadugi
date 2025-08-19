"""Error handling utilities."""
from typing import Any, Optional, Dict
import logging

class ErrorHandler:
    """Basic error handler for agent operations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle an error with context."""
        self.logger.error(f"Error: {error}")
        if context:
            self.logger.error(f"Context: {context}")

    def create_error_result(self, error: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {"success": False, "error": error}
