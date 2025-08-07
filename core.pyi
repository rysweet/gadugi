from typing import Any, List

"""
Expanded static-type stub for the legacy ``core`` module.

It provides all classes and enumerations referenced by test-suites
(e.g. PR backlog manager tests) and uses a universal ``__getattr__``
fallback so Pyright does not complain about unrecognised attributes.
"""

# ---------------------------------------------------------------------------#
# Exceptions
# ---------------------------------------------------------------------------#
class GadugiError(Exception): ...

# ---------------------------------------------------------------------------#
# Pull-Request backlog domain models
# ---------------------------------------------------------------------------#
class PRStatus:
    READY: PRStatus
    BLOCKED: PRStatus
    PROCESSING: PRStatus

class ReadinessCriteria:
    NO_MERGE_CONFLICTS: ReadinessCriteria
    CI_PASSING: ReadinessCriteria
    UP_TO_DATE: ReadinessCriteria
    HUMAN_REVIEW_COMPLETE: ReadinessCriteria
    AI_REVIEW_COMPLETE: ReadinessCriteria
    METADATA_COMPLETE: ReadinessCriteria

class BacklogMetrics: ...

class PRAssessment:
    status: PRStatus
    readiness: ReadinessCriteria
    metrics: BacklogMetrics

    def __init__(
        self,
        pr_number: int = ...,
        status: PRStatus = ...,
        criteria_met: dict = ...,
        blocking_issues: list = ...,
        resolution_actions: list = ...,
        last_updated: Any = ...,
        processing_time: Any = ...,
    ) -> None: ...

class PRBacklogManager:
    auto_approve: bool

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    # Methods referenced in tests
    def assess(self, pr_number: int) -> PRAssessment: ...
    def update_backlog(self) -> None: ...
    def get_metrics(self) -> BacklogMetrics: ...

# ---------------------------------------------------------------------------#
# Generic system-initialisation helpers (placeholder)
# ---------------------------------------------------------------------------#
class CoreSystem:
    def start(self) -> None: ...
    def stop(self) -> None: ...

def initialize(*args: Any, **kwargs: Any) -> CoreSystem: ...

# ---------------------------------------------------------------------------#
# Unknown attribute fallback
# ---------------------------------------------------------------------------#
from typing import Any as _Any  # noqa: E402

def __getattr__(name: str) -> _Any:  # type: ignore[override]
    ...  # type: ignore[return-value]

__all__: List[str] = []
