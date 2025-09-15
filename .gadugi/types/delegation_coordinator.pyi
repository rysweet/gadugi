from enum import Enum
from typing import Any, List, Protocol, runtime_checkable

"""
Stub for legacy ``delegation_coordinator`` module referenced by the
PR backlog manager test-suite.

It defines all enums/classes accessed in tests and returns ``Any`` for
any unknown attribute to avoid Pyright unknown-member reports.
"""

# ---------------------------------------------------------------------------#
# Enumerations referenced by tests
# ---------------------------------------------------------------------------#
class DelegationType(Enum):
    MERGE_CONFLICT_RESOLUTION = "merge_conflict_resolution"
    CI_FAILURE_FIX = "ci_failure_fix"
    BRANCH_UPDATE = "branch_update"
    AI_CODE_REVIEW = "ai_code_review"
    METADATA_IMPROVEMENT = "metadata_improvement"

class DelegationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

# ---------------------------------------------------------------------------#
# Core data model
# ---------------------------------------------------------------------------#
class DelegationTask:
    task_id: str
    task_type: DelegationType
    agent_target: str
    prompt_template: str
    context: dict[str, Any]
    retry_count: int

# ---------------------------------------------------------------------------#
# Coordinator interface / concrete shim
# ---------------------------------------------------------------------------#
@runtime_checkable
class DelegationCoordinatorProtocol(Protocol):
    def delegate(self, task: DelegationTask, *, auto_approve: bool = ...) -> str: ...

class DelegationCoordinator:
    def delegate(self, task: DelegationTask, *, auto_approve: bool = ...) -> str: ...

def get_default() -> DelegationCoordinator: ...

# ---------------------------------------------------------------------------#
# Unknown attribute fallback
# ---------------------------------------------------------------------------#
from typing import Any as _Any  # noqa: E402

def __getattr__(name: str) -> _Any:  # type: ignore[override]
    ...  # type: ignore[return-value]

__all__: List[str] = []
