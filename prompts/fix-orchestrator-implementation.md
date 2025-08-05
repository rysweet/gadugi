# Fix Orchestrator Implementation

## Context
Issues #27 and #102 have identified that the orchestrator-agent doesn't work because:
1. The orchestrator-agent.md file contains only pseudo-code documentation
2. Python components exist (ExecutionEngine, WorktreeManager, etc.) but aren't properly coordinated
3. No actual implementation to spawn WorkflowManager processes or monitor execution

## Current State Analysis

### What Exists:
- **ExecutionEngine** (.claude/orchestrator/components/execution_engine.py) - Can spawn subprocess tasks
- **WorktreeManager** (.claude/orchestrator/components/worktree_manager.py) - Can create git worktrees
- **TaskAnalyzer** (.claude/orchestrator/components/task_analyzer.py) - Can analyze task dependencies
- **PromptGenerator** (.claude/orchestrator/components/prompt_generator.py) - Can generate workflow prompts
- **StateManager** (.claude/shared/state_management.py) - Can persist state

### What's Missing:
- Main orchestrator coordinator that ties components together
- Process registry to track running agents
- Monitoring capability for real-time visibility
- Checkpoint/resume functionality
- File-based coordination mechanisms

## Design Decision: Staged vs Complete Implementation

### Option 1: Complete the Pseudo-Code (Quick Fix)
- Create orchestrator.py that implements the pseudo-code from orchestrator-agent.md
- Wire up existing components with minimal changes
- Get basic parallel execution working quickly
- **Pros**: Fast to implement, uses existing design
- **Cons**: Doesn't address core visibility/monitoring issues

### Option 2: Follow Issue #27 Staged Approach (Recommended)
- Stage 1: Enhanced Process Registry
- Stage 2: VS Code Integration API
- Stage 3: Checkpoint/Resume
- Stage 4: Dependency Management
- Stage 5: Container Integration
- **Pros**: Addresses real problems, provides visibility, enables recovery
- **Cons**: More work, staged implementation

## Recommended Implementation Plan

### Phase 1: Minimal Orchestrator Coordinator (1-2 days)
Create a working orchestrator that:
1. Accepts list of prompt files
2. Uses TaskAnalyzer to analyze dependencies
3. Uses WorktreeManager to create isolated environments
4. Uses ExecutionEngine to spawn WorkflowManager processes
5. Provides basic progress output

### Phase 2: Enhanced Process Registry (Stage 1 from Issue #27)
1. Extend ExecutionEngine with process metadata tracking
2. Create `.gadugi/monitoring/registry.json` with running tasks
3. Add heartbeat mechanism to track agent health
4. Implement file-watching for VS Code integration

### Phase 3: Real-time Monitoring (Stage 2 from Issue #27)
1. Create monitoring directory structure
2. Stream task output to log files
3. Write progress JSON files
4. Enable VS Code to watch and display status

## Implementation Strategy

### Step 1: Create Minimal Working Orchestrator
```python
# .claude/orchestrator/orchestrator_main.py
class OrchestratorCoordinator:
    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        self.worktree_manager = WorktreeManager()
        self.execution_engine = ExecutionEngine()
        self.registry = ProcessRegistry()  # New component

    def orchestrate(self, prompt_files):
        # 1. Analyze tasks
        tasks = self.task_analyzer.analyze_prompts(prompt_files)

        # 2. Create worktrees
        for task in tasks:
            self.worktree_manager.create_worktree(task.id, task.branch)

        # 3. Execute with monitoring
        self.registry.start_monitoring()
        results = self.execution_engine.execute_tasks_parallel(
            tasks,
            self.worktree_manager,
            progress_callback=self.registry.update_progress
        )

        # 4. Cleanup
        self.cleanup_worktrees(tasks)
        return results
```

### Step 2: Add Process Registry
```python
# .claude/orchestrator/components/process_registry.py
class ProcessRegistry:
    def __init__(self):
        self.registry_file = Path(".gadugi/monitoring/registry.json")
        self.tasks = {}

    def register_task(self, task_id, pid, worktree):
        self.tasks[task_id] = {
            "pid": pid,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat(),
            "worktree": str(worktree)
        }
        self._save_registry()

    def _save_registry(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(self.tasks, f, indent=2)
```

### Step 3: Integration Script
Create a script that can be invoked when `/agent:orchestrator-agent` is called:
```bash
#!/bin/bash
# .claude/orchestrator/run_orchestrator.sh
python .claude/orchestrator/orchestrator_main.py "$@"
```

## Success Criteria
1. Can invoke orchestrator with list of prompts
2. Creates worktrees for parallel execution
3. Spawns WorkflowManager agents in parallel
4. Provides real-time visibility of running tasks
5. Tracks process status in registry file
6. Handles errors gracefully
7. Cleans up worktrees after completion

## Deliverables
1. Working orchestrator_main.py that coordinates components
2. ProcessRegistry for tracking running agents
3. Integration script for Claude invocation
4. Basic monitoring file output
5. Documentation of how to use the orchestrator
6. Test demonstrating parallel execution works
