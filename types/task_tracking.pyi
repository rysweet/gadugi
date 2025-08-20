from enum import Enum
from typing import Any, Dict, List
import typing_extensions

# Basic enums reflecting runtime constants
class TaskStatus(Enum): ...
class Priority(Enum): ...

# Core data model
class Task: ...
class TaskTracker: ...

# Shared helper/result types imported elsewhere
class OperationResult: ...
class ValidationResult: ...

# Convenience aliases
Metadata: typing_extensions.TypeAlias = Dict[str, Any]

__all__: List[str] = []
