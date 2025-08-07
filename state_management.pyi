from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import typing_extensions

# Exceptions
class StateError(Exception): ...
class StateValidationError(StateError): ...

# Enumeration for workflow phases
class WorkflowPhase(Enum): ...

# Core data model
class TaskState: ...
class StateManager: ...
class CheckpointManager: ...

# Helper type aliases (mirroring runtime module behaviour)
DateTimeStr = str
JSONDict: typing_extensions.TypeAlias = Dict[str, Any]

# Public attributes list for wildcard imports
__all__: List[str] = []
