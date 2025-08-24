"""State manager for incremental builds and caching."""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .recipe_model import Recipe

logger = logging.getLogger(__name__)


@dataclass
class BuildState:
    """State of a single recipe build."""
    recipe_name: str
    checksum: str
    success: bool
    timestamp: str
    build_time: float
    changed: bool = False
    error: Optional[str] = None
    files_generated: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BuildState':
        """Create from dictionary."""
        return cls(**data)


class StateManager:
    """Manages build state, caching, and incremental builds."""
    
    def __init__(self, state_dir: Path = Path(".recipe-state")):
        """Initialize state manager.
        
        Args:
            state_dir: Directory for state storage
        """
        self.state_dir = state_dir
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / "build_state.json"
        self._state: Dict[str, BuildState] = self._load_state()
        
    def _load_state(self) -> Dict[str, BuildState]:
        """Load state from disk.
        
        Returns:
            Dictionary of recipe name to build state
        """
        if not self.state_file.exists():
            return {}
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            
            state = {}
            for name, state_data in data.items():
                state[name] = BuildState.from_dict(state_data)
            
            logger.debug(f"Loaded state for {len(state)} recipes")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {}
    
    def _save_state(self):
        """Save state to disk."""
        try:
            data = {}
            for name, state in self._state.items():
                data[name] = state.to_dict()
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved state for {len(self._state)} recipes")
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def needs_rebuild(self, recipe: Recipe, force: bool = False) -> bool:
        """Check if recipe needs rebuilding based on checksums.
        
        Args:
            recipe: Recipe to check
            force: Force rebuild regardless of state
            
        Returns:
            True if recipe needs rebuilding
        """
        if force:
            logger.debug(f"{recipe.name}: Forced rebuild")
            return True
        
        # Check if recipe has been built before
        if recipe.name not in self._state:
            logger.debug(f"{recipe.name}: Never built before")
            return True
        
        state = self._state[recipe.name]
        
        # Check if recipe files changed (via checksum)
        current_checksum = recipe.get_checksum()
        if current_checksum != state.checksum:
            logger.debug(f"{recipe.name}: Checksum changed")
            return True
        
        # Check if any dependencies changed
        for dep_name in recipe.get_dependencies():
            if dep_name in self._state:
                if self._state[dep_name].changed:
                    logger.debug(f"{recipe.name}: Dependency {dep_name} changed")
                    return True
        
        # Check if previous build failed
        if not state.success:
            logger.debug(f"{recipe.name}: Previous build failed")
            return True
        
        # Check if too old (optional staleness check)
        if self._is_stale(state):
            logger.debug(f"{recipe.name}: Build is stale")
            return True
        
        logger.debug(f"{recipe.name}: No rebuild needed")
        return False
    
    def _is_stale(self, state: BuildState, max_age_days: int = 7) -> bool:
        """Check if build state is too old.
        
        Args:
            state: Build state to check
            max_age_days: Maximum age in days
            
        Returns:
            True if state is stale
        """
        try:
            build_time = datetime.fromisoformat(state.timestamp)
            age = datetime.now() - build_time
            return age.days > max_age_days
        except:
            return True
    
    def record_build(self, recipe: Recipe, result):
        """Record build result for caching and incremental builds.
        
        Args:
            recipe: Recipe that was built
            result: Build result
        """
        # Create build state
        state = BuildState(
            recipe_name=recipe.name,
            checksum=recipe.get_checksum(),
            success=result.success,
            timestamp=datetime.now().isoformat(),
            build_time=result.build_time,
            changed=True,  # Mark as changed for dependent recipes
            error=result.errors[0] if result.errors else None,
            files_generated=len(result.code.get_all_files()) if result.code else 0
        )
        
        # Update state
        self._state[recipe.name] = state
        
        # Save generated artifacts if successful
        if result.success and result.code:
            self._save_artifacts(recipe, result.code)
        
        # Persist state
        self._save_state()
        
        logger.info(f"Recorded build state for {recipe.name}: "
                   f"{'success' if result.success else 'failed'}")
    
    def _save_artifacts(self, recipe: Recipe, code):
        """Save generated code artifacts for caching.
        
        Args:
            recipe: Recipe that was built
            code: Generated code
        """
        artifact_dir = self.state_dir / recipe.name
        artifact_dir.mkdir(exist_ok=True)
        
        # Save all generated files
        for filepath, content in code.get_all_files().items():
            artifact_path = artifact_dir / filepath
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(content)
        
        # Save metadata
        metadata = {
            "recipe_name": recipe.name,
            "timestamp": datetime.now().isoformat(),
            "files": list(code.get_all_files().keys()),
            "language": code.language
        }
        
        metadata_path = artifact_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.debug(f"Saved {len(code.get_all_files())} artifacts for {recipe.name}")
    
    def get_cached_code(self, recipe_name: str) -> Optional[Dict[str, str]]:
        """Get cached code for a recipe.
        
        Args:
            recipe_name: Name of recipe
            
        Returns:
            Dictionary of file paths to content, or None if not cached
        """
        artifact_dir = self.state_dir / recipe_name
        if not artifact_dir.exists():
            return None
        
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            files = {}
            for filepath in metadata.get("files", []):
                file_path = artifact_dir / filepath
                if file_path.exists():
                    files[filepath] = file_path.read_text()
            
            logger.debug(f"Loaded {len(files)} cached files for {recipe_name}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to load cached code for {recipe_name}: {e}")
            return None
    
    def clear_state(self, recipe_name: Optional[str] = None):
        """Clear build state.
        
        Args:
            recipe_name: Specific recipe to clear, or None for all
        """
        if recipe_name:
            # Clear specific recipe
            if recipe_name in self._state:
                del self._state[recipe_name]
                logger.info(f"Cleared state for {recipe_name}")
            
            # Remove artifacts
            artifact_dir = self.state_dir / recipe_name
            if artifact_dir.exists():
                import shutil
                shutil.rmtree(artifact_dir)
                logger.info(f"Removed artifacts for {recipe_name}")
        else:
            # Clear all state
            self._state = {}
            logger.info("Cleared all build state")
            
            # Remove all artifacts
            for artifact_dir in self.state_dir.iterdir():
                if artifact_dir.is_dir() and artifact_dir.name != ".git":
                    import shutil
                    shutil.rmtree(artifact_dir)
        
        self._save_state()
    
    def mark_unchanged(self, recipe_name: str):
        """Mark a recipe as unchanged (for dependency tracking).
        
        Args:
            recipe_name: Recipe to mark
        """
        if recipe_name in self._state:
            self._state[recipe_name].changed = False
            self._save_state()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get state statistics.
        
        Returns:
            Statistics about cached builds
        """
        if not self._state:
            return {
                "total_cached": 0,
                "successful": 0,
                "failed": 0,
                "total_files": 0
            }
        
        successful = sum(1 for s in self._state.values() if s.success)
        failed = sum(1 for s in self._state.values() if not s.success)
        total_files = sum(s.files_generated for s in self._state.values())
        
        # Calculate cache size
        cache_size = 0
        for artifact_dir in self.state_dir.iterdir():
            if artifact_dir.is_dir():
                for file in artifact_dir.rglob("*"):
                    if file.is_file():
                        cache_size += file.stat().st_size
        
        return {
            "total_cached": len(self._state),
            "successful": successful,
            "failed": failed,
            "total_files": total_files,
            "cache_size_mb": round(cache_size / 1024 / 1024, 2)
        }