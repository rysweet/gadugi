"""State management for Recipe Executor builds."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import json
import hashlib
from datetime import datetime

from .recipe_model import Recipe, SingleBuildResult


@dataclass
class BuildState:
    """State of a recipe build."""

    recipe_name: str
    recipe_checksum: str
    build_time: datetime
    success: bool
    outputs: List[str] = field(default_factory=lambda: [])
    errors: List[str] = field(default_factory=lambda: [])


class StateManager:
    """Manages build state and caching."""

    def __init__(self, state_dir: Optional[Path] = None):
        """Initialize state manager."""
        self.state_dir = state_dir or Path(".recipe_build")
        self.state_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, BuildState] = {}
        self._load_state()

    def needs_rebuild(self, recipe: Recipe, force: bool = False) -> bool:
        """Check if recipe needs rebuilding."""
        if force:
            return True

        # Check if we have a previous build
        if recipe.name not in self._cache:
            return True

        previous = self._cache[recipe.name]

        # Check if recipe files changed (via checksum)
        current_checksum = self._calculate_recipe_checksum(recipe)
        if current_checksum != previous.recipe_checksum:
            return True

        # Check if previous build failed
        if not previous.success:
            return True

        # Check if dependencies changed
        # This would need to recursively check dependency checksums
        # For now, simplified implementation

        return False

    def record_build(self, recipe: Recipe, result: SingleBuildResult) -> None:
        """Record build result for caching."""
        checksum = self._calculate_recipe_checksum(recipe)

        state = BuildState(
            recipe_name=recipe.name,
            recipe_checksum=checksum,
            build_time=datetime.now(),
            success=result.success,
            outputs=list(result.code.files.keys()) if result.code else [],
            errors=result.errors,
        )

        self._cache[recipe.name] = state
        self._save_state()

    def get_last_build(self, recipe_name: str) -> Optional[BuildState]:
        """Get information about last build."""
        return self._cache.get(recipe_name)

    def clear_cache(self, recipe_name: Optional[str] = None) -> None:
        """Clear build cache."""
        if recipe_name:
            if recipe_name in self._cache:
                del self._cache[recipe_name]
        else:
            self._cache.clear()

        self._save_state()

    def _calculate_recipe_checksum(self, recipe: Recipe) -> str:
        """Calculate checksum for recipe content."""
        hasher = hashlib.sha256()

        # Hash recipe content
        hasher.update(recipe.requirements.purpose.encode())
        hasher.update(recipe.design.architecture.encode())
        hasher.update(json.dumps(recipe.components.dependencies).encode())

        # Include metadata checksum if available
        if recipe.metadata.checksum:
            hasher.update(recipe.metadata.checksum.encode())

        return hasher.hexdigest()

    def _load_state(self) -> None:
        """Load state from disk."""
        state_file = self.state_dir / "state.json"

        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)

                for name, state_data in data.items():
                    self._cache[name] = BuildState(
                        recipe_name=state_data["recipe_name"],
                        recipe_checksum=state_data["recipe_checksum"],
                        build_time=datetime.fromisoformat(state_data["build_time"]),
                        success=state_data["success"],
                        outputs=state_data.get("outputs", []),
                        errors=state_data.get("errors", []),
                    )
            except Exception as e:
                print(f"Warning: Failed to load state: {e}")

    def _save_state(self) -> None:
        """Save state to disk."""
        state_file = self.state_dir / "state.json"

        data = {}
        for name, state in self._cache.items():
            data[name] = {
                "recipe_name": state.recipe_name,
                "recipe_checksum": state.recipe_checksum,
                "build_time": state.build_time.isoformat(),
                "success": state.success,
                "outputs": state.outputs,
                "errors": state.errors,
            }

        try:
            with open(state_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save state: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get build statistics."""
        total = len(self._cache)
        successful = sum(1 for s in self._cache.values() if s.success)
        failed = total - successful

        return {
            "total_builds": total,
            "successful": successful,
            "failed": failed,
            "recipes": list(self._cache.keys()),
        }
