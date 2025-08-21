#
# Minimal static-type stub for the **docker** SDK.
# Provides only the attributes referenced in this codebase so
# Pyright can resolve imports during static analysis.  Runtime
# functionality is **not** implemented.
#

from typing import Any, List

# ------------------------------------------------------------------
# Client classes
# ------------------------------------------------------------------
class DockerClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def containers(self) -> ContainerCollection: ...

class APIClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    # Generic catch-all for attribute access in tests
    def __getattr__(self, name: str) -> Any: ...

# ------------------------------------------------------------------
# Container abstraction (subset)
# ------------------------------------------------------------------
class Container:
    id: str
    name: str
    status: str

    def logs(self, *args: Any, **kwargs: Any) -> bytes: ...
    def start(self, *args: Any, **kwargs: Any) -> None: ...
    def stop(self, *args: Any, **kwargs: Any) -> None: ...
    def remove(self, *args: Any, **kwargs: Any) -> None: ...
    def exec_run(self, cmd: str | List[str], **kwargs: Any) -> ExecResult: ...

class ContainerCollection:
    def run(
        self,
        image: str,
        command: str | List[str] | None = ...,
        detach: bool | None = ...,
        **kwargs: Any,
    ) -> Container: ...
    def get(self, container_id: str) -> Container: ...

class ExecResult:
    exit_code: int
    output: bytes

# Convenience helper
def from_env() -> DockerClient: ...

# Fallback for any attribute we didn't declare
def __getattr__(name: str) -> Any: ...

__all__: List[str] = []
