#!/usr/bin/env python3
"""
Memory-GitHub Integration Configuration Management

This module handles configuration for the Memory.md to GitHub Issues integration,
including sync policies, pruning rules, and operational parameters.
"""

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from sync_engine import ConflictResolution, SyncDirection


@dataclass
class CompactionConfig:
    """Configuration for automatic Memory.md compaction"""

    # Size thresholds for triggering compaction
    max_lines: int = 100  # Maximum lines before compaction
    max_chars: int = 50000  # Maximum characters before compaction
    target_lines: int = 80  # Target lines after compaction
    min_benefit: float = 0.2  # Minimum reduction percentage to proceed

    # Compaction behavior
    enable_auto_compaction: bool = True
    create_backup: bool = True
    details_file_name: str = "LongTermMemoryDetails.md"

    # Section-specific compaction rules
    section_rules: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "Current Goals": {"preserve_all": True, "max_age_days": None},
            "Next Steps": {"preserve_all": True, "max_age_days": None},
            "Completed Tasks": {"max_age_days": 7, "max_items": 15},
            "Recent Accomplishments": {"max_age_days": 14, "max_items": 20},
            "Reflections": {"max_age_days": 30, "max_items": 10},
            "Important Context": {"max_items": 15, "preserve_high_priority": True},
            "Code Review Summary": {"max_age_days": 21, "max_items": 5},
        }
    )


@dataclass
class PruningConfig:
    """Configuration for Memory.md content pruning (legacy - use CompactionConfig)"""

    completed_task_age_days: int = 7
    reflection_age_days: int = 30
    max_accomplishments: int = 20
    max_context_items: int = 15
    preserve_high_priority: bool = True
    preserve_issue_references: bool = True
    preserve_recent_count: int = 10

    # Section-specific rules
    section_rules: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "Current Goals": {"max_items": 10, "preserve_all": True},
            "Completed Tasks": {"max_age_days": 7, "max_items": 20},
            "Recent Accomplishments": {"max_age_days": 14, "max_items": 15},
            "Reflections": {"max_age_days": 30, "consolidate_similar": True},
            "Important Context": {"relevance_scoring": True, "max_items": 15},
            "Next Steps": {"preserve_all": True},
        }
    )


@dataclass
class SyncConfig:
    """Configuration for Memory.md-GitHub synchronization"""

    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    conflict_resolution: ConflictResolution = ConflictResolution.MANUAL
    auto_create_issues: bool = True
    auto_close_completed: bool = True
    sync_frequency_minutes: int = 5
    batch_size: int = 10
    backup_before_sync: bool = True
    dry_run: bool = False

    # Rate limiting
    api_delay_seconds: float = 0.1
    max_retries: int = 3
    retry_delay_seconds: int = 2

    # Section filtering
    include_sections: List[str] = field(default_factory=list)
    exclude_sections: List[str] = field(
        default_factory=lambda: ["Reflections", "Important Context"]
    )


@dataclass
class IssueCreationConfig:
    """Configuration for GitHub issue creation"""

    default_labels: List[str] = field(
        default_factory=lambda: ["memory-sync", "ai-assistant"]
    )
    priority_labels: bool = True
    auto_assign: bool = False
    assignee: Optional[str] = None
    template_name: str = "memory-task"

    # Issue content
    include_context: bool = True
    include_metadata: bool = True
    max_title_length: int = 80

    # Labels by priority
    priority_label_map: Dict[str, str] = field(
        default_factory=lambda: {
            "high": "priority:high",
            "medium": "priority:medium",
            "low": "priority:low",
        }
    )


@dataclass
class ContentRules:
    """Rules for Memory.md content management"""

    required_sections: List[str] = field(
        default_factory=lambda: [
            "Current Goals",
            "Recent Accomplishments",
            "Next Steps",
        ]
    )
    optional_sections: List[str] = field(
        default_factory=lambda: [
            "Completed Tasks",
            "Reflections",
            "Important Context",
            "Code Review Summary",
        ]
    )

    # Task patterns
    completed_patterns: List[str] = field(default_factory=lambda: ["✅", "[x]"])
    pending_patterns: List[str] = field(default_factory=lambda: ["[ ]", "- [ ]"])
    priority_patterns: List[str] = field(
        default_factory=lambda: ["**CRITICAL**", "**HIGH**", "**URGENT**"]
    )

    # Content limits
    max_items_per_section: int = 50
    max_file_size_kb: int = 500

    # Formatting
    maintain_chronological_order: bool = True
    preserve_context_links: bool = True
    normalize_task_format: bool = True


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and logging"""

    enable_logging: bool = True
    log_level: str = "INFO"
    log_file: Optional[str] = "memory-sync.log"

    # Metrics
    track_sync_performance: bool = True
    track_conflict_rates: bool = True
    track_api_usage: bool = True

    # Alerting
    alert_on_conflicts: bool = True
    alert_on_failures: bool = True
    alert_email: Optional[str] = None


@dataclass
class MemoryManagerConfig:
    """Complete configuration for Memory Manager"""

    # Core components
    compaction: CompactionConfig = field(default_factory=CompactionConfig)
    pruning: PruningConfig = field(default_factory=PruningConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    issue_creation: IssueCreationConfig = field(default_factory=IssueCreationConfig)
    content_rules: ContentRules = field(default_factory=ContentRules)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Paths
    memory_file_path: str = ".github/Memory.md"
    config_file_path: str = ".github/MemoryManager/config.yaml"
    state_directory: str = ".github/memory-sync-state"
    backup_directory: str = ".github/memory-sync-state/backups"

    # Operational
    enabled: bool = True
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        # Convert enums to strings before calling asdict to ensure proper YAML serialization
        sync_dict = asdict(self.sync)
        if hasattr(self.sync.direction, "value"):
            sync_dict["direction"] = self.sync.direction.value
        if hasattr(self.sync.conflict_resolution, "value"):
            sync_dict["conflict_resolution"] = self.sync.conflict_resolution.value

        # Create the full dictionary
        result = asdict(self)
        result["sync"] = sync_dict

        return result

    def save_to_file(self, file_path: str):
        """Save configuration to YAML file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)

    @classmethod
    def load_from_file(cls, file_path: str) -> "MemoryManagerConfig":
        """Load configuration from YAML file"""
        path = Path(file_path)
        if not path.exists():
            # Return default config if file doesn't exist
            return cls()

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Convert nested dictionaries back to dataclasses
        config = cls()

        if "compaction" in data:
            config.compaction = CompactionConfig(**data["compaction"])
        if "pruning" in data:
            config.pruning = PruningConfig(**data["pruning"])
        if "sync" in data:
            # Handle enum conversion
            sync_data = data["sync"].copy()
            if "direction" in sync_data:
                sync_data["direction"] = SyncDirection(sync_data["direction"])
            if "conflict_resolution" in sync_data:
                sync_data["conflict_resolution"] = ConflictResolution(
                    sync_data["conflict_resolution"]
                )
            config.sync = SyncConfig(**sync_data)
        if "issue_creation" in data:
            config.issue_creation = IssueCreationConfig(**data["issue_creation"])
        if "content_rules" in data:
            config.content_rules = ContentRules(**data["content_rules"])
        if "monitoring" in data:
            config.monitoring = MonitoringConfig(**data["monitoring"])

        # Update other fields
        for field_name in [
            "memory_file_path",
            "config_file_path",
            "state_directory",
            "backup_directory",
            "enabled",
            "version",
        ]:
            if field_name in data:
                setattr(config, field_name, data[field_name])

        return config


class ConfigManager:
    """Manages Memory Manager configuration"""

    DEFAULT_CONFIG_LOCATIONS = [
        ".github/MemoryManager/config.yaml",
        ".github/MemoryManager/config.yml",
        ".MemoryManager.yaml",
        ".MemoryManager.yml",
    ]

    def __init__(self, repo_path: str = None, config_path: str = None):
        """Initialize configuration manager"""
        self.repo_path = Path(repo_path or os.getcwd())
        self.config_path = config_path
        self.config: Optional[MemoryManagerConfig] = None

    def load_config(self) -> MemoryManagerConfig:
        """Load configuration from file or create default"""
        if self.config is not None:
            return self.config

        # Try to find config file
        config_file = self._find_config_file()

        if config_file:
            print(f"Loading config from: {config_file}")
            self.config = MemoryManagerConfig.load_from_file(config_file)
        else:
            print("No config file found, using defaults")
            self.config = MemoryManagerConfig()

            # Create default config file
            default_path = self.repo_path / self.DEFAULT_CONFIG_LOCATIONS[0]
            self.config.save_to_file(str(default_path))
            print(f"Created default config at: {default_path}")

        return self.config

    def save_config(self, config: MemoryManagerConfig = None):
        """Save configuration to file"""
        if config:
            self.config = config

        if not self.config:
            raise ValueError("No configuration to save")

        config_file = self._find_config_file() or (
            self.repo_path / self.DEFAULT_CONFIG_LOCATIONS[0]
        )
        self.config.save_to_file(str(config_file))

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in standard locations"""
        if self.config_path:
            path = Path(self.config_path)
            return path if path.exists() else None

        for location in self.DEFAULT_CONFIG_LOCATIONS:
            path = self.repo_path / location
            if path.exists():
                return path

        return None

    def validate_config(self, config: MemoryManagerConfig = None) -> List[str]:
        """Validate configuration and return any errors"""
        cfg = config or self.config
        if not cfg:
            return ["No configuration loaded"]

        errors = []

        # Validate paths
        memory_path = self.repo_path / cfg.memory_file_path
        if not memory_path.exists():
            errors.append(f"Memory file not found: {memory_path}")

        # Validate sync configuration
        if cfg.sync.batch_size <= 0:
            errors.append("Batch size must be positive")

        if cfg.sync.sync_frequency_minutes <= 0:
            errors.append("Sync frequency must be positive")

        # Validate pruning configuration
        if cfg.pruning.completed_task_age_days < 0:
            errors.append("Completed task age cannot be negative")

        # Validate content rules
        if cfg.content_rules.max_items_per_section <= 0:
            errors.append("Max items per section must be positive")

        return errors

    def get_effective_config(self) -> Dict[str, Any]:
        """Get effective configuration with all resolved values"""
        config = self.load_config()
        effective = config.to_dict()

        # Resolve relative paths
        effective["memory_file_path"] = str(self.repo_path / config.memory_file_path)
        effective["state_directory"] = str(self.repo_path / config.state_directory)
        effective["backup_directory"] = str(self.repo_path / config.backup_directory)

        return effective


def create_default_config() -> MemoryManagerConfig:
    """Create default configuration with sensible defaults"""
    return MemoryManagerConfig(
        pruning=PruningConfig(
            completed_task_age_days=7,
            preserve_high_priority=True,
            max_accomplishments=20,
        ),
        sync=SyncConfig(
            direction=SyncDirection.BIDIRECTIONAL,
            conflict_resolution=ConflictResolution.MANUAL,
            auto_create_issues=True,
            sync_frequency_minutes=5,
        ),
        issue_creation=IssueCreationConfig(
            default_labels=["memory-sync", "ai-assistant", "automated"],
            priority_labels=True,
        ),
        content_rules=ContentRules(
            max_items_per_section=30, maintain_chronological_order=True
        ),
        monitoring=MonitoringConfig(enable_logging=True, track_sync_performance=True),
    )


def main():
    """Example usage of configuration system"""
    try:
        # Initialize config manager
        manager = ConfigManager("/Users/ryan/src/gadugi")

        # Load configuration
        config = manager.load_config()

        print("Configuration loaded:")
        print(f"  Memory file: {config.memory_file_path}")
        print(f"  Sync direction: {config.sync.direction.value}")
        print(f"  Auto create issues: {config.sync.auto_create_issues}")
        print(f"  Conflict resolution: {config.sync.conflict_resolution.value}")

        # Validate configuration
        errors = manager.validate_config()
        if errors:
            print("\nConfiguration errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\nConfiguration is valid ✅")

        # Show effective configuration
        effective = manager.get_effective_config()
        print(f"\nEffective memory file path: {effective['memory_file_path']}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
