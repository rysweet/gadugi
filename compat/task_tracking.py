"""
Compatibility shim for legacy `task_tracking` imports.

This module dynamically loads and re-exports the canonical implementation
located at `.claude/shared/task_tracking.py`.  Existing code that does:

    from task_tracking import Task, TaskTracker

continues to work unchanged while the authoritative implementation lives
under the Enhanced Separation directory.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_IMPL_PATH = (
    Path(__file__).resolve().parent.parent / ".claude" / "shared" / "task_tracking.py"
)

if not _IMPL_PATH.is_file():  # pragma: no cover
    raise ImportError(f"Canonical implementation not found at {_IMPL_PATH}")

_spec = importlib.util.spec_from_file_location("_gadugi_task_tracking_impl", _IMPL_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Unable to load spec for {_IMPL_PATH}")

_module = importlib.util.module_from_spec(_spec)
assert isinstance(_module, ModuleType)
sys.modules[_spec.name] = _module  # Register early
_spec.loader.exec_module(_module)  # type: ignore[arg-type]

# Re-export public names so star-imports still work.
globals().update({k: v for k, v in _module.__dict__.items() if not k.startswith("_")})
__all__ = [name for name in globals() if not name.startswith("_")]
