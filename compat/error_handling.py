import importlib.util
import sys

"""
Compatibility shim for legacy `error_handling` imports.

This module dynamically loads and re-exports the canonical implementation
located at `.claude/shared/utils/error_handling.py`.  Keeping this wrapper
allows existing code that does:

    from error_handling import GadugiError, retry

to continue working while preserving a single source-of-truth
implementation under the Enhanced Separation directory.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

# Absolute path to the real implementation inside the Enhanced Separation tree.
_IMPL_PATH = (
    Path(__file__)
    .resolve()
    .parent.parent  # Go up one more level since we're now in compat/
    / ".claude"
    / "shared"
    / "utils"
    / "error_handling.py"
)

if not _IMPL_PATH.is_file():  # pragma: no cover
    raise ImportError(f"Canonical implementation not found at {_IMPL_PATH}")

_spec = importlib.util.spec_from_file_location(
    "_gadugi_error_handling_impl", _IMPL_PATH
)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Unable to load spec for {_IMPL_PATH}")

_module = importlib.util.module_from_spec(_spec)
assert isinstance(_module, ModuleType)
# Register early to avoid duplicate module loads elsewhere.
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)  # type: ignore[arg-type]

# Re-export every public attribute so star-imports still work.
globals().update({k: v for k, v in _module.__dict__.items() if not k.startswith("_")})
__all__ = [name for name in globals() if not name.startswith("_")]
