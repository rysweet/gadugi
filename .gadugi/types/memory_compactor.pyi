from typing import Any, List

"""
Expanded stub for legacy `memory_compactor` module used in tests.
Declares all classes, methods, and attributes referenced by the test suite,
including CompactionRule, parser, and all dynamic attributes.
"""

class CompactionRule:
    name: str
    threshold: int
    section_name: str
    max_age_days: int
    max_items: int
    preserve_patterns: list[str]
    priority_preserve: bool

    def __init__(
        self,
        name: str,
        threshold: int,
        section_name: str = ...,
        max_age_days: int = ...,
        max_items: int = ...,
        preserve_patterns: list[str] = ...,
        priority_preserve: bool = ...,
    ) -> None: ...
    def should_preserve(self, *args: Any, **kwargs: Any) -> bool: ...

class MemoryCompactor:
    memory_path: str
    details_path: str
    rules: List[CompactionRule]
    size_thresholds: dict[str, int]
    parser: Any

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def compact(self, data: List[Any]) -> List[Any]: ...
    def statistics(self) -> dict[str, Any]: ...
    def compact_memory(self, *args: Any, **kwargs: Any) -> Any: ...
    def needs_compaction(self, *args: Any, **kwargs: Any) -> bool: ...
    def _extract_section_items(self, *args: Any, **kwargs: Any) -> Any: ...
    def _estimate_item_age(self, *args: Any, **kwargs: Any) -> Any: ...
    def _archive_items(self, *args: Any, **kwargs: Any) -> Any: ...
    def _create_compacted_memory(self, *args: Any, **kwargs: Any) -> Any: ...

def get_default() -> MemoryCompactor: ...

__all__: List[str] = []

from typing import Any as _Any

def __getattr__(name: str) -> _Any:  # type: ignore[override]
    ...  # type: ignore[return-value]
