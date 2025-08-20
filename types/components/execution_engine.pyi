from typing import Any, List, Protocol, runtime_checkable

"""
Static type stub for legacy ``components.execution_engine``.

It contains only the symbols referenced by the test-suite.  Every unknown
attribute fallback returns ``typing.Any`` so Pyright will not complain about
missing members.
"""

# ---------------------------------------------------------------------------#
# Core result / protocol types
# ---------------------------------------------------------------------------#
class ExecutionResult: ...
class TaskExecutor: ...

@runtime_checkable
class ExecutionEngineProtocol(Protocol):
    def execute(self, task: Any, *, dry_run: bool | None = ...) -> ExecutionResult: ...
    def cancel(self, task_id: str) -> bool: ...
    def status(self, task_id: str) -> dict[str, Any]: ...

class ExecutionEngine:  # Concrete shim for tests that instantiate
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def execute(self, task: Any, *, dry_run: bool | None = ...) -> ExecutionResult: ...
    def cancel(self, task_id: str) -> bool: ...
    def status(self, task_id: str) -> dict[str, Any]: ...

# Free-standing helper used in tests
def run_workflow(*args: Any, **kwargs: Any) -> ExecutionResult: ...

# ---------------------------------------------------------------------------#
# Fallback for any attribute not explicitly declared
# ---------------------------------------------------------------------------#
from typing import Any as _Any  # noqa: E402  (allowed in .pyi context)

def __getattr__(name: str) -> _Any:  # type: ignore[override]
    ...  # type: ignore[return-value]

__all__: List[str] = []
