from typing import Any, List, Protocol, runtime_checkable

"""
Static stub for legacy ``components.prompt_generator`` referenced by tests.
Only type information is provided—no runtime implementation.
"""

# ---------------------------------------------------------------------------#
# Core types surfaced to tests
# ---------------------------------------------------------------------------#
class Prompt:
    content: str

class PromptContext:
    task_id: str
    metadata: dict[str, Any]

class PromptGenerator:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    # Methods explicitly accessed in tests
    def create_context_from_task(self, task: Any) -> PromptContext: ...
    def generate_workflow_prompt(self, context: PromptContext) -> Prompt: ...

@runtime_checkable
class PromptGeneratorProtocol(Protocol):
    def create_context_from_task(self, task: Any) -> PromptContext: ...
    def generate_workflow_prompt(self, context: PromptContext) -> Prompt: ...

# Free-standing helpers referenced
def create_context_from_task(task: Any) -> PromptContext: ...
def generate_workflow_prompt(context: PromptContext) -> Prompt: ...

# ---------------------------------------------------------------------------#
# Fallback for unknown attributes to silence Pyright reportAttributeAccessIssue
# ---------------------------------------------------------------------------#
from typing import Any as _Any  # noqa: E402  (allowed in .pyi context)

def __getattr__(name: str) -> _Any:  # type: ignore[override]
    ...  # type: ignore[return-value]

__all__: List[str] = []
