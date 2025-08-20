"""
Compatibility shim for legacy `xpia_defense` imports.

Loads and re-exports the canonical implementation found in
`.claude/shared/xpia_defense.py`.  This keeps older tests such as
`tests/test_xpia_defense.py` working without modifying their import
statements.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_IMPL_PATH = (
    Path(__file__).resolve().parent.parent / ".claude" / "shared" / "xpia_defense.py"
)

if not _IMPL_PATH.is_file():  # pragma: no cover
    raise ImportError(f"Canonical implementation not found at {_IMPL_PATH}")

_spec = importlib.util.spec_from_file_location("_gadugi_xpia_defense_impl", _IMPL_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Unable to load spec for {_IMPL_PATH}")

_module = importlib.util.module_from_spec(_spec)
assert isinstance(_module, ModuleType)
sys.modules[_spec.name] = _module  # Prevent duplicate loads
_spec.loader.exec_module(_module)  # type: ignore[arg-type]

# Re-export public names so `from xpia_defense import XpiaDefense` works.
globals().update({k: v for k, v in _module.__dict__.items() if not k.startswith("_")})
__all__ = [name for name in globals() if not name.startswith("_")]
