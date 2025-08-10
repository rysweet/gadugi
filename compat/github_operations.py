"""
Compatibility shim for legacy `github_operations` imports.

This thin wrapper dynamically loads the canonical implementation located at
`.claude/shared/github_operations.py` and re-exports its public symbols.

It allows existing code that does `import github_operations` or
`from github_operations import GitHubOperations` to keep working without
changing the import paths, while maintaining a single source of truth.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_IMPL_PATH = (
    Path(__file__).resolve().parent.parent
    / ".claude"
    / "shared"
    / "github_operations.py"
)

if not _IMPL_PATH.is_file():
    raise ImportError(f"Canonical implementation not found at {_IMPL_PATH}")

_spec = importlib.util.spec_from_file_location(
    "_gadugi_github_operations_impl", _IMPL_PATH
)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Unable to load spec for {_IMPL_PATH}")

_module = importlib.util.module_from_spec(_spec)
assert isinstance(_module, ModuleType)
sys.modules[_spec.name] = _module  # Register to avoid duplicate loads
_spec.loader.exec_module(_module)  # type: ignore[arg-type]

# Re-export every public attribute so star-imports still work.
globals().update({k: v for k, v in _module.__dict__.items() if not k.startswith("_")})
__all__ = [name for name in globals() if not name.startswith("_")]

# Fallback for static type checkers – dynamically expose missing attributes
from typing import Any as _Any


def __getattr__(name: str) -> _Any:  # type: ignore[misc]
    """Return attribute from underlying implementation or Any for unknown names."""
    return getattr(_module, name, _Any)  # noqa: ANN001

