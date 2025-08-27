# Agent Development Instructions

## When to Load This File
Load when you need to:
- Create new agents
- Modify existing agents
- Debug agent issues
- Understand agent patterns

## Agent Structure

### Required YAML Frontmatter
```yaml
---
name: agent-name
specialization: Specific purpose
tools: Read, Write, Edit, Bash, Grep
---
```

### Agent File Template
```markdown
---
name: my-agent
specialization: Handles specific task type
tools: Read, Write, Edit, Bash
---

# My Agent

## Specialization
Clear description of what this agent does.

## Approach
1. Step-by-step methodology
2. Decision criteria
3. Success metrics

## Usage
'''
/agent:my-agent

Context: Specific problem context
Requirements: What needs to be achieved
'''
```

## Common Agent Types

### General-Purpose Agent
```
subagent_type: general-purpose
- For complex, multi-step tasks
- Can use all available tools
- Good for research and implementation
```

### Workflow Manager
```
subagent_type: workflow-manager
- Executes 13-phase workflow
- Creates issues, PRs
- Manages development lifecycle
```

### Code Reviewer
```
subagent_type: code-reviewer
- Reviews pull requests
- Provides feedback
- Checks best practices
```

## Agent Registration

### Validation Requirements
```bash
# Check YAML frontmatter exists
head -n 10 agent-file.md | grep "^---"

# Validate in CI
.github/workflows/validate-agents.yml
```

### Common Registration Issues
- Missing YAML frontmatter
- Invalid YAML syntax
- Missing required fields
- File not in correct directory

## Agent Testing

### Mock Pattern
```python
class MockAgent:
    def __init__(self):
        self.called = False
        self.args = None
    
    def invoke(self, *args, **kwargs):
        self.called = True
        self.args = (args, kwargs)
        return {"success": True}
```

### Integration Testing
```python
def test_agent_invocation():
    # Don't mock registration
    agent = load_agent("agent-name")
    assert agent is not None
    
    # Then test execution
    result = agent.execute(task)
    assert result["success"]
```

## Agent Communication

### Using Task Tool
```python
# Spawn parallel agent instances
Task(
    subagent_type="general-purpose",
    description="Fix component",
    prompt="Detailed instructions..."
)
```

### Agent Delegation
```
# From one agent to another
/agent:workflow-manager

Delegated from orchestrator
Task: Execute workflow for prompt.md
```

## Best Practices

### 1. Single Responsibility
- One agent = one clear purpose
- Don't create mega-agents
- Compose complex workflows from simple agents

### 2. Clear Documentation
- Document inputs/outputs
- Provide usage examples
- List required tools

### 3. Error Handling
- Graceful degradation
- Clear error messages
- Recovery procedures

### 4. State Management
- Use `.task/` directories
- Save progress regularly
- Enable resumption

## Debugging Agents

### Check Registration
```bash
# List registered agents
ls -la .claude/agents/*.md
ls -la .github/agents/*.md

# Validate frontmatter
grep -l "^---" .claude/agents/*.md
```

### Test Invocation
```
/agent:agent-name

Test: Simple test task
Debug: Enable verbose output
```

### Common Issues
1. **Import errors**: Check tool availability
2. **State corruption**: Clean `.task/` directory
3. **Timeout**: Increase max-turns parameter
4. **Memory**: Check context size

## Agent Patterns

### Research Agent
- Uses Read, Grep, Glob extensively
- Doesn't modify files
- Returns analysis results

### Implementation Agent
- Uses Write, Edit, MultiEdit
- Creates/modifies code
- Runs tests

### Orchestration Agent
- Uses Task tool
- Spawns other agents
- Coordinates parallel work

### Review Agent
- Uses Read, Grep
- Analyzes code quality
- Provides feedback

## Performance Tips

1. **Minimize context**: Pass only needed info
2. **Early validation**: Check prereqs first
3. **Batch operations**: Multiple edits at once
4. **Parallel execution**: Use Task tool
5. **Cache results**: Save to `.task/` directory