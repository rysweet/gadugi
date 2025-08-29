# How to Use v0.3 RIGHT NOW in This Conversation

## You're Currently Using Main Branch
Right now, you're talking to Claude on the main branch, but v0.3 features are available in PR #184.

## To Switch to Using v0.3:

### Option 1: Merge and Use v0.3
```bash
# Merge PR #184 to main
gh pr merge 184

# Pull latest
git pull

# Activate v0.3
./activate_v03.sh
```

### Option 2: Tell Claude to Use v0.3 Features
Even without merging, you can tell me to use v0.3 patterns:

## Examples of Using v0.3 vs Not Using It

### ❌ NOT Using v0.3 (Current/Manual Way)
```
You: "Fix all the type errors in the codebase"
Claude: [Manually goes through files one by one, takes 20 minutes]
```

### ✅ USING v0.3 (Parallel/Orchestrated Way)
```
You: "Use v0.3 orchestrator to fix all type errors in parallel"
Claude: [Spawns 5 parallel tasks, completes in 5 minutes]
```

### ❌ NOT Using v0.3 (No Memory)
```
You: "What did we decide about the architecture?"
Claude: "I don't have that context from previous conversations"
```

### ✅ USING v0.3 (With Memory)
```
You: "Store this architecture decision in v0.3 memory: We're using event-driven architecture"
Claude: [Stores in memory system]

Later...
You: "Recall our architecture decisions from v0.3 memory"
Claude: [Retrieves: "Event-driven architecture"]
```

## Concrete Examples You Can Try Now

### 1. Parallel Task Execution
```
"Use v0.3 Task tool to parallelize these tasks:
- Create a new agent for monitoring
- Add tests for memory system
- Document the orchestrator"
```

### 2. Workflow Management
```
"Use v0.3 workflow-manager pattern to:
- Create a new feature branch
- Implement feature X
- Create PR with proper testing"
```

### 3. Memory Storage
```
"Initialize v0.3 memory and store:
- Project goal: Build v0.4 with enhanced agent communication
- Decision: Use message queues for agent communication
- Learning: Parallel execution is 3-5x faster"
```

### 4. Agent Invocation
```
"Use the task-decomposer agent pattern to break down:
'Build v0.4 agent communication system' into parallel tasks"
```

## The Key Insight

**Main Branch (Current)**: You manually direct Claude step-by-step
**v0.3 Branch (Available)**: You give high-level goals, v0.3 orchestrates execution

## Real Example: Building a v0.4 Feature

### Without v0.3:
```
You: Create an agent message bus
Claude: [Creates single file]
You: Now add tests
Claude: [Creates test file]
You: Now add documentation
Claude: [Creates docs]
Total time: 30 minutes, sequential
```

### With v0.3:
```
You: "Use v0.3 orchestrator to create agent message bus with tests and docs"
Claude: [Uses Task tool to spawn 3 parallel instances]
  - Task 1: Create message bus implementation
  - Task 2: Create comprehensive tests
  - Task 3: Create documentation
Total time: 10 minutes, parallel
```

## Try This Right Now:

Ask me: "Use the v0.3 Task tool pattern to create 3 parallel tasks for building the v0.4 monitoring system"

Or: "Create a v0.3 memory-enabled workflow for implementing feature X"

Or: "Show me how v0.3 orchestrator would handle refactoring the entire codebase"

## Why This Matters

v0.3 isn't just code - it's a new WAY of working:
- **Parallel instead of sequential**
- **Memory-persistent instead of stateless**
- **Self-orchestrated instead of manually directed**
- **Agent-composed instead of monolithic**

You built v0.3 to build v0.4 faster. Now use it!
