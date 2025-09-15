from typing import Any, List, Protocol, runtime_checkable

"""
Stub for legacy ``components.worktree_manager`` referenced by the test-suite.

It defines the concrete/Protocol APIs exercised by tests and falls back
to ``typing.Any`` for any unknown attribute, preventing Pyright
``reportAttributeAccessIssue`` errors.
"""

# ---------------------------------------------------------------------------#
# Core data model
# ---------------------------------------------------------------------------#
class Worktree:
    path: str
    branch: str
    worktree_path: str
    branch_name: str

    def __init__(
        self,
        path: str,
        branch: str,
        worktree_path: str = ...,
        branch_name: str = ...,
        task_id: str = ...,
    ) -> None: ...

# ---------------------------------------------------------------------------#
# Public manager protocols/classes
# ---------------------------------------------------------------------------#
@runtime_checkable
class WorktreeManagerProtocol(Protocol):
    def create_worktree(
        self,
        path: str,
        branch: str,
        *,
        checkout: bool = ...,
        task_id: str = ...,
        worktree_path: str = ...,
        prompt_file: str = ...,
        task_context: Any = ...,
    ) -> Worktree: ...
    def cleanup_worktree(self, wt: Worktree, *, force: bool = ...) -> None: ...
    def list_worktrees(self) -> List[Worktree]: ...

class WorktreeManager:  # Concrete shim for tests that instantiate
    def create_worktree(
        self,
        path: str,
        branch: str,
        *,
        checkout: bool = ...,
        task_id: str = ...,
        worktree_path: str = ...,
        prompt_file: str = ...,
        task_context: Any = ...,
    ) -> Worktree: ...
    def cleanup_worktree(self, wt: Worktree, *, force: bool = ...) -> None: ...
    def list_worktrees(self) -> List[Worktree]: ...

# Factory/helper referenced in tests
def get_manager(*args: Any, **kwargs: Any) -> WorktreeManager: ...

# ---------------------------------------------------------------------------#
# Unknown attribute fallback
# ---------------------------------------------------------------------------#
from typing import Any as _Any  # noqa: E402

def __getattr__(name: str) -> _Any:  # type: ignore[override]
    ...  # type: ignore[return-value]

__all__: List[str] = []
