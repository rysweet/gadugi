TaskData(
    id="11",
    content="🔧 AUTOMATIC: Update Claude settings (Phase 11)",
    status="pending",
    priority="medium",
    phase=WorkflowPhase.SETTINGS_UPDATE,
    auto_invoke=True,
    enforcement_level="OPTIONAL"  # Settings update is beneficial but not critical
),
TaskData(
    id="12",
    content="📦 AUTOMATIC: Compact Memory.md if needed (Phase 12)",
    status="pending",
    priority="low",
    phase=WorkflowPhase.MEMORY_COMPACTION,
    auto_invoke=True,
    enforcement_level="MAINTENANCE"  # Memory compaction is automated maintenance
)
