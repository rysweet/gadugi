#!/usr/bin/env python3
"""Code Executor - Single-purpose executor for code file operations.

This executor performs direct file operations without delegating to other agents.
It follows the NO DELEGATION principle - all operations use direct tool/file access.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from .base_executor import BaseExecutor


class CodeExecutor(BaseExecutor):
    """Single-purpose executor for writing and editing code files.

    CRITICAL: This executor MUST NOT call or delegate to other agents.
    All operations must be direct file system operations only.
    """

    def __init__(self):
        """Initialize the code executor."""
        self.operations_log = []

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution entry point.

        Args:
            params: Dictionary containing:
                - action: 'write' | 'edit' | 'read'
                - file_path: Path to the file
                - content: Content to write (for write/edit)
                - old_content: Content to replace (for edit)

        Returns:
            Dictionary with:
                - success: Boolean indicating success
                - file_path: Path to the affected file
                - action: Action performed
                - error: Error message if failed
        """
        action = params.get("action", "write")
        file_path = params.get("file_path")

        if not file_path:
            return {"success": False, "error": "file_path is required"}

        # Convert to Path object for consistent handling
        path = Path(file_path)

        try:
            if action == "write":
                return self._write_file(path, params.get("content", ""))
            elif action == "edit":
                return self._edit_file(
                    path, params.get("old_content", ""), params.get("new_content", "")
                )
            elif action == "read":
                return self._read_file(path)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {
                "success": False,
                "file_path": str(path),
                "action": action,
                "error": str(e),
            }

    def _write_file(self, path: Path, content: str) -> Dict[str, Any]:
        """Write content to a file.

        Direct file system operation - no agent delegation.
        """
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file already exists
        if path.exists():
            return {
                "success": False,
                "file_path": str(path),
                "action": "write",
                "error": f"File already exists: {path}",
            }

        # Write the content
        path.write_text(content, encoding="utf-8")

        # Log the operation
        self._log_operation("write", str(path))

        return {
            "success": True,
            "file_path": str(path),
            "action": "write",
            "bytes_written": len(content.encode("utf-8")),
        }

    def _edit_file(
        self, path: Path, old_content: str, new_content: str
    ) -> Dict[str, Any]:
        """Edit an existing file by replacing content.

        Direct file system operation - no agent delegation.
        """
        if not path.exists():
            return {
                "success": False,
                "file_path": str(path),
                "action": "edit",
                "error": f"File does not exist: {path}",
            }

        # Read current content
        current_content = path.read_text(encoding="utf-8")

        # Check if old_content exists in file
        if old_content not in current_content:
            return {
                "success": False,
                "file_path": str(path),
                "action": "edit",
                "error": "Old content not found in file",
            }

        # Replace content
        updated_content = current_content.replace(old_content, new_content, 1)

        # Write back
        path.write_text(updated_content, encoding="utf-8")

        # Log the operation
        self._log_operation("edit", str(path))

        return {
            "success": True,
            "file_path": str(path),
            "action": "edit",
            "changes_made": 1,
        }

    def _read_file(self, path: Path) -> Dict[str, Any]:
        """Read content from a file.

        Direct file system operation - no agent delegation.
        """
        if not path.exists():
            return {
                "success": False,
                "file_path": str(path),
                "action": "read",
                "error": f"File does not exist: {path}",
            }

        content = path.read_text(encoding="utf-8")

        # Log the operation
        self._log_operation("read", str(path))

        return {
            "success": True,
            "file_path": str(path),
            "action": "read",
            "content": content,
            "size_bytes": len(content.encode("utf-8")),
        }

    def _log_operation(self, operation: str, file_path: str):
        """Log an operation for audit purposes."""
        self.operations_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "file_path": file_path,
            }
        )

    def get_operations_log(self) -> List[Dict[str, str]]:
        """Get the log of all operations performed."""
        return self.operations_log.copy()


# Single-purpose function interface for direct usage
def execute_code_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a code operation without creating an instance.

    This is the primary interface for CLAUDE.md orchestration.
    No agent delegation - direct file operations only.

    Args:
        params: Operation parameters

    Returns:
        Operation result dictionary
    """
    executor = CodeExecutor()
    return executor.execute(params)
