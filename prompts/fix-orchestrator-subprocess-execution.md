# Fix Orchestrator Subprocess Execution for Real Parallel Workflows

## Title and Overview
**Orchestrator Real Subprocess Execution Implementation**

Fix the orchestrator agent to properly spawn actual subprocess instances instead of returning text responses, enabling true parallel workflow execution with proper WorkflowManager delegation.

## Problem Statement

The current orchestrator implementation fails to execute real subprocess instances:
- **Returns text instead of spawning processes**: Orchestrator generates text responses rather than actually invoking subprocess Claude instances
- **No real parallel execution**: ThreadPoolExecutor calls don't spawn actual Claude CLI processes
- **Missing WorkflowManager delegation**: Direct execution bypasses mandatory 11-phase workflow requirement
- **No subprocess monitoring**: No real process tracking or output streaming
- **Fake parallelism**: Simulated parallel execution without actual concurrent processes

**CRITICAL GOVERNANCE VIOLATION**: The orchestrator MUST delegate ALL task execution to WorkflowManager instances to ensure proper workflow phases are followed (Issue #148).

## Technical Analysis

### Current Orchestrator Issues

1. **Text Generation Instead of Process Spawning**:
```python
# WRONG: Current implementation
def execute_workflow(task):
    return f"Executing workflow for {task.name}"  # Just returns text!

# CORRECT: Should spawn actual process
def execute_workflow(task):
    process = subprocess.Popen([
        "claude", "-p", task.prompt_file,
        "--dangerously-skip-permissions",
        "--max-turns", "50"
    ])
    return process
```

2. **Missing WorkflowManager Delegation**:
```python
# WRONG: Direct execution bypassing workflow phases
result = execute_task_directly(task)

# CORRECT: Mandatory WorkflowManager delegation
result = spawn_workflow_manager_process(task)
```

3. **No Real Process Management**:
```python
# WRONG: Fake process tracking
def track_process(task_id):
    return {"status": "running", "fake": True}

# CORRECT: Real subprocess monitoring
def track_process(process):
    return {
        "pid": process.pid,
        "returncode": process.poll(),
        "real_process": True
    }
```

## Requirements

### 1. Real Subprocess Spawning
- Use `subprocess.Popen` or similar to spawn actual Claude CLI processes
- Each task must run in separate process with proper isolation
- Support concurrent process execution with resource limits
- Implement proper process lifecycle management

### 2. Mandatory WorkflowManager Delegation
```bash
# Each spawned process MUST use WorkflowManager
claude -p /agent:workflow-manager \
  --dangerously-skip-permissions \
  --max-turns 50 \
  --verbose
```

### 3. Process Monitoring and Control
- Real-time process status tracking
- Output streaming from parallel processes
- Resource usage monitoring (CPU, memory)
- Process cleanup and termination handling

### 4. Proper Parallel Architecture
```python
class RealOrchestratorEngine:
    def __init__(self):
        self.active_processes = {}
        self.process_monitor = ProcessMonitor()

    def execute_parallel_tasks(self, tasks):
        processes = []
        for task in tasks:
            # MANDATORY: Delegate to WorkflowManager
            process = self.spawn_workflow_manager(task)
            processes.append(process)
            self.active_processes[task.id] = process

        return self.monitor_parallel_execution(processes)
```

### 5. UV Environment Integration
All subprocess execution must use UV environment:
```bash
# Each spawned process in UV context
cd worktree_path && uv run claude -p /agent:workflow-manager
```

## Implementation Plan

### Phase 1: Process Spawning Infrastructure
- Replace text generation with real `subprocess.Popen` calls
- Implement proper Claude CLI invocation with all required flags
- Add process lifecycle management (start, monitor, cleanup)
- Create process registry for tracking active subprocesses

### Phase 2: WorkflowManager Integration
- Update all task execution to use `/agent:workflow-manager`
- Ensure 11-phase workflow execution for every task
- Add governance validation to prevent direct execution
- Implement proper worktree isolation for each process

### Phase 3: Real-time Monitoring System
- Implement live process status tracking
- Add output streaming from subprocess stdout/stderr
- Create process resource monitoring (CPU, memory, disk)
- Build process health checks and error detection

### Phase 4: Parallel Execution Engine
- Implement true parallel process execution
- Add resource limiting and process scheduling
- Create proper error handling and recovery
- Implement graceful process termination

### Phase 5: Integration and Testing
- Full end-to-end testing with real parallel processes
- Performance validation (3-5x speedup verification)
- Resource usage optimization and limits
- Error scenario testing and recovery

## Architecture Components

### ProcessManager Class
```python
class ProcessManager:
    def __init__(self):
        self.processes = {}
        self.monitor = ProcessMonitor()

    def spawn_workflow_manager(self, task):
        """Spawn real WorkflowManager subprocess"""
        cmd = [
            "claude", "-p", "/agent:workflow-manager",
            "--dangerously-skip-permissions",
            "--max-turns", "50",
            "--verbose"
        ]

        # Add task context as environment variables
        env = os.environ.copy()
        env["ORCHESTRATOR_TASK_ID"] = task.id
        env["ORCHESTRATOR_WORKTREE"] = task.worktree_path

        process = subprocess.Popen(
            cmd,
            cwd=task.worktree_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self.processes[task.id] = process
        return process
```

### ProcessMonitor Class
```python
class ProcessMonitor:
    def __init__(self):
        self.monitors = {}

    def start_monitoring(self, task_id, process):
        """Start real-time process monitoring"""
        monitor_thread = threading.Thread(
            target=self._monitor_process,
            args=(task_id, process)
        )
        monitor_thread.start()
        self.monitors[task_id] = monitor_thread

    def _monitor_process(self, task_id, process):
        """Monitor actual subprocess execution"""
        while process.poll() is None:
            # Stream output in real-time
            output = process.stdout.readline()
            if output:
                self._log_process_output(task_id, output.strip())
            time.sleep(0.1)
```

## Files to Modify

### Core Orchestrator Files
1. **`.claude/orchestrator/orchestrator_main.py`**:
   - Replace fake execution with real subprocess spawning
   - Add ProcessManager integration
   - Implement proper error handling

2. **`.claude/orchestrator/components/execution_engine.py`**:
   - Replace ThreadPoolExecutor text generation with process spawning
   - Add real parallel process management
   - Implement subprocess monitoring

3. **`.claude/orchestrator/process_registry.py`**:
   - Update to track real processes instead of fake entries
   - Add process status and health monitoring
   - Implement proper process cleanup

### New Components
1. **`.claude/orchestrator/process_manager.py`**: ProcessManager class
2. **`.claude/orchestrator/process_monitor.py`**: ProcessMonitor class
3. **`.claude/orchestrator/subprocess_executor.py`**: Subprocess execution utilities

## Success Criteria

### Functional Requirements
- **Real subprocess spawning**: Actual Claude CLI processes launched
- **WorkflowManager delegation**: Every task uses proper workflow phases
- **True parallelism**: Multiple concurrent processes executing simultaneously
- **Process monitoring**: Real-time tracking of subprocess status and output

### Performance Requirements
- **3-5x speedup**: Achieved through real parallel execution
- **Resource efficiency**: Proper process resource limits and monitoring
- **Subprocess isolation**: Complete separation between parallel tasks
- **Error recovery**: Proper handling of subprocess failures

### Governance Requirements
- **Workflow compliance**: ALL tasks follow 11-phase WorkflowManager workflow
- **No direct execution**: Zero instances of bypassing WorkflowManager
- **Quality gates**: Proper testing and validation in each workflow phase
- **State tracking**: Complete workflow state management

## Testing Requirements

### Process Execution Testing
```bash
# Test real subprocess spawning
python -m pytest tests/test_orchestrator_subprocess.py

# Validate WorkflowManager delegation
python -m pytest tests/test_workflow_delegation.py

# Test parallel execution performance
python -m pytest tests/test_parallel_performance.py
```

### Integration Testing
- Verify real Claude CLI processes are spawned
- Test subprocess output streaming works correctly
- Validate process cleanup and resource management
- Ensure WorkflowManager receives proper task context

### Performance Testing
- Benchmark parallel vs sequential execution times
- Monitor subprocess resource usage
- Test system behavior under load
- Validate 3-5x speedup claims with real measurements

## Risk Mitigation

### Process Management Risks
- **Subprocess cleanup**: Ensure no orphaned processes
- **Resource limits**: Prevent system resource exhaustion
- **Error propagation**: Proper error handling across process boundaries
- **Process termination**: Graceful shutdown of all subprocesses

### Integration Risks
- **WorkflowManager compatibility**: Ensure proper delegation works
- **UV environment isolation**: Maintain proper virtual environment context
- **State synchronization**: Coordinate state between orchestrator and subprocesses
- **Output handling**: Prevent output mixing between parallel processes

## Implementation Steps

1. **Create ProcessManager class** with real subprocess spawning
2. **Update ExecutionEngine** to use ProcessManager instead of text generation
3. **Add ProcessMonitor** for real-time subprocess tracking
4. **Implement WorkflowManager delegation** for all task execution
5. **Add UV environment support** for subprocess execution
6. **Create comprehensive testing** for subprocess functionality
7. **Performance validation** with real parallel execution benchmarks
8. **Documentation updates** for new subprocess architecture

---

*This prompt fixes the orchestrator to perform real subprocess execution with proper WorkflowManager delegation, achieving true parallel workflow execution while maintaining governance compliance.*
