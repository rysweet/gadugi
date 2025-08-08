# AI Assistant Instructions Template

This template shows how to integrate Gadugi agents and instructions into your project's CLAUDE.md.

## Example CLAUDE.md Structure

```markdown
# AI Assistant Instructions

⚠️ **FIRST ACTION**: Check and update `.github/Memory.md` ! ⚠️

⚠️ **SECOND ACTION**: When working on Claude agents or instructions, read https://docs.anthropic.com/en/docs/claude-code/memory ! ⚠️

---

## Generic Claude Code Instructions

@https://raw.githubusercontent.com/rysweet/gadugi/main/claude-generic-instructions.md

## Agent Hierarchy

@https://raw.githubusercontent.com/rysweet/gadugi/main/docs/architecture/AGENT_HIERARCHY.md

## Project-Specific Instructions

[Your project-specific instructions here]

## Available Agents from Gadugi

When you need specialized agents, use:
- `/agent:workflow-manager` - For complete development workflows
- `/agent:orchestrator-agent` - For parallel task execution
- `/agent:code-reviewer` - For code review tasks
- `/agent:prompt-writer` - For creating structured prompts
- `/agent:agent-manager` - For managing agent updates

## Agent Manager Configuration

To keep agents updated from Gadugi:
1. Run `/agent:agent-manager init`
2. Register Gadugi: `/agent:agent-manager register-repo https://github.com/rysweet/gadugi`
3. Install agents: `/agent:agent-manager install all`
```

## Integration Steps

1. **Create your CLAUDE.md** based on this template
2. **Configure Agent Manager** to sync from Gadugi
3. **Import generic instructions** using @ syntax
4. **Add project-specific rules** below the imports
5. **Set up hooks** for automatic agent updates
