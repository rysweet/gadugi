from types import TracebackType
from typing import (
    Any,
    Callable,
    ContextManager,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

_T = TypeVar("_T")
_E = TypeVar("_E", bound=BaseException)

#
# Minimal static-type stub for the external **pytest** library.
# It is *not* a runtime replacement—only satisfies Pyright’s import
# and attribute-access checks within the project’s test suite.
#

# ---------------------------
# Core decorators and helpers
# ---------------------------
def fixture(
    func: Callable[..., _T] | None = None,
    *,
    scope: str | None = ...,
    autouse: bool | None = ...,
    params: Sequence[Any] | None = ...,
) -> Callable[..., _T]: ...
def mark(**kwargs: Any) -> Any: ...

# ---------------------------
# Assertions / exception utils
# ---------------------------
class raises(ContextManager[None]):  # noqa: N801
    def __init__(
        self,
        expected_exception: type[_E] | Tuple[type[_E], ...],
        match: str | None = ...,
    ) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool: ...

# ---------------------------
# Monkeypatch helper (stub)
# ---------------------------
class MonkeyPatch:
    def setattr(
        self, target: str | Any, name: str | Any = ..., value: Any = ..., **kwargs: Any
    ) -> None: ...
    def setenv(
        self, name: str, value: str | None, *, prepend: str | None = ...
    ) -> None: ...
    def delenv(self, name: str, *, raising: bool = ...) -> None: ...
    def syspath_prepend(self, path: str) -> None: ...

# ---------------------------
# Main API surface
# ---------------------------
class _MarkDecorator:
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
    def __getattr__(self, name: str) -> _MarkDecorator: ...

class _Mark:
    def __getattr__(self, name: str) -> _MarkDecorator: ...
    def __call__(self, *args: Any, **kwargs: Any) -> _MarkDecorator: ...

mark = _Mark()  # type: ignore[assignment]

# Dynamic attribute fallback for unknown helpers (parametrize, skip, etc.)
def __getattr__(name: str) -> Any: ...

__all__: List[str] = []
