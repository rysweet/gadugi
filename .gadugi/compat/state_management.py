"""
Compatibility shim for legacy `state_management` imports.

This module re-exports the canonical implementation located at
`.claude/shared/state_management.py` so that existing code written
before the Enhanced Separation refactor can continue to use the simple
import path:

    import state_management

or:

    from state_management import StateManager

Keeping this thin wrapper avoids widespread changes while ensuring that
there is a single source of truth for the implementation.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_IMPL_PATH = Path(__file__).resolve().parent.parent / ".claude" / "shared" / "state_management.py"

if not _IMPL_PATH.is_file():
    raise ImportError(f"Canonical implementation not found at {_IMPL_PATH}")

_spec = importlib.util.spec_from_file_location("_gadugi_state_mgmt_impl", _IMPL_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Unable to load spec for {_IMPL_PATH}")

_module = importlib.util.module_from_spec(_spec)
assert isinstance(_module, ModuleType)
sys.modules[_spec.name] = _module  # Register to avoid duplicate loads
_spec.loader.exec_module(_module)  # type: ignore[arg-type]

# Re-export public names so `from state_management import X` continues to work.
globals().update({k: v for k, v in _module.__dict__.items() if not k.startswith("_")})
__all__ = [name for name in globals() if not name.startswith("_")]
