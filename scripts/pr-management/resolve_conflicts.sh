#!/bin/bash

echo "Resolving merge conflicts for PR #296..."

# Function to resolve conflicts by keeping both versions where appropriate
resolve_conflicts() {
    local file="$1"
    local strategy="$2"
    
    if [[ ! -f "$file" ]]; then
        echo "File not found: $file"
        return 1
    fi
    
    case "$strategy" in
        "theirs")
            # Keep the v0.3-regeneration version
            git checkout --theirs "$file"
            git add "$file"
            echo "✓ Resolved $file (kept v0.3-regeneration version)"
            ;;
        "ours")
            # Keep our TeamCoach version
            git checkout --ours "$file"
            git add "$file"
            echo "✓ Resolved $file (kept TeamCoach version)"
            ;;
        "merge")
            # Manual merge needed - we'll handle these specially
            echo "⚠ $file needs manual merge"
            ;;
    esac
}

# Memory files - keep v0.3-regeneration version as it's more complete
resolve_conflicts ".github/Memory.md" "theirs"
resolve_conflicts ".github/MemoryManager/config.py" "theirs"
resolve_conflicts ".github/MemoryManager/github_integration.py" "theirs"
resolve_conflicts ".github/MemoryManager/memory_compactor.py" "theirs"
resolve_conflicts ".github/MemoryManager/memory_manager.py" "theirs"
resolve_conflicts ".github/MemoryManager/sync_engine.py" "theirs"

# Service files - keep our TeamCoach implementations as they're newer
resolve_conflicts ".claude/services/event-router/event_router.py" "ours"
resolve_conflicts ".claude/services/event-router/models.py" "ours"
resolve_conflicts ".claude/services/mcp/mcp_service.py" "ours"
resolve_conflicts "neo4j/test_connection.py" "ours"

# Gadugi event service - keep theirs as it has type fixes
resolve_conflicts "gadugi/event_service/agent_invoker.py" "theirs"
resolve_conflicts "gadugi/event_service/cli.py" "theirs"
resolve_conflicts "gadugi/event_service/events.py" "theirs"
resolve_conflicts "gadugi/event_service/github_client.py" "theirs"
resolve_conflicts "gadugi/event_service/handlers.py" "theirs"
resolve_conflicts "gadugi/event_service/service.py" "theirs"

# Test files - keep theirs for type safety improvements
resolve_conflicts "tests/agents/pr_backlog_manager/test_stubs.py" "theirs"
resolve_conflicts "tests/agents/system_design_reviewer/test_core.py" "theirs"
resolve_conflicts "tests/agents/test_claude_settings_update.py" "theirs"
resolve_conflicts "tests/agents/test_readme_agent.py" "theirs"
resolve_conflicts "tests/conftest.py" "theirs"
resolve_conflicts "tests/event_service/test_handlers.py" "theirs"
resolve_conflicts "tests/integration/test_enhanced_separation_basic.py" "theirs"
resolve_conflicts "tests/integration/test_enhanced_separation_basic_broken.py" "theirs"
resolve_conflicts "tests/integration/test_orchestrator_agent_enhanced_separation.py" "theirs"
resolve_conflicts "tests/integration/test_workflow_manager_enhanced_separation.py" "theirs"
resolve_conflicts "tests/memory_manager/test_memory_compactor.py" "theirs"
resolve_conflicts "tests/shared/test_error_handling.py" "theirs"
resolve_conflicts "tests/shared/test_github_operations.py" "theirs"
resolve_conflicts "tests/shared/test_interfaces.py" "theirs"
resolve_conflicts "tests/shared/test_phase_enforcer.py" "theirs"
resolve_conflicts "tests/shared/test_task_tracking.py" "theirs"
resolve_conflicts "tests/shared/test_workflow_engine.py" "theirs"
resolve_conflicts "tests/shared/test_workflow_validator.py" "theirs"
resolve_conflicts "tests/test_enhanced_workflow_manager_reliability.py" "theirs"
resolve_conflicts "tests/test_program_manager.py" "theirs"

# Config files - keep theirs for consistency
resolve_conflicts ".pre-commit-config.yaml" "theirs"
resolve_conflicts "pyproject.toml" "theirs"
resolve_conflicts "pyrightconfig.json" "theirs"
resolve_conflicts "uv.lock" "theirs"

# Core files - keep theirs
resolve_conflicts "src/gadugi/agent_interface.py" "theirs"

# Prompts - keep ours
resolve_conflicts "prompts/implement-mcp-service.md" "ours"

# Files that were deleted in our branch but modified in theirs - accept deletion
git rm benchmark_performance.py 2>/dev/null || true
git rm pytest.pyi 2>/dev/null || true
git rm test_orchestrator_fix_integration.py 2>/dev/null || true

# Handle file location conflicts
git rm .claude/prompts/agent-framework-implementation.md 2>/dev/null || true
git rm .claude/prompts/memory-system-integration.md 2>/dev/null || true

echo ""
echo "Conflict resolution complete!"
echo "Remaining conflicts to check:"
git status --short | grep "^UU"