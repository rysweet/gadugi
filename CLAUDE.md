# AI Assistant Instructions

This file combines generic Claude Code best practices with project-specific instructions for the AI-SIP workshop repository.

⚠️ **FIRST ACTION**: Check and update @.github/Memory.md ! ⚠️
⚠️ **NEW**: Memory.md now syncs with GitHub Issues via MemoryManagerAgent! ⚠️

⚠️ **SECOND ACTION**: When working on Claude agents or instructions, read https://docs.anthropic.com/en/docs/claude-code/memory ! ⚠️

---

## CRITICAL: Workflow Execution Pattern

**For ANY development task that requires multiple phases (issue, branch, code, PR):**

1. **DO NOT manually execute workflow phases**
2. **Use the proper agent hierarchy**:
   
   **For multiple tasks or when parallelization is possible**:
   ```
   /agent:orchestrator-agent
   
   Execute these specific prompts in parallel:
   - prompt-file-1.md
   - prompt-file-2.md
   ```
   
   **For single sequential tasks**:
   ```
   /agent:workflow-manager
   
   Task: Execute workflow for /prompts/[prompt-file].md
   ```

3. **Agent Hierarchy**:
   - **OrchestratorAgent**: Top-level coordinator for parallel execution
   - **WorkflowManager**: Handles individual workflow execution
   - **Code-Reviewer**: Executes Phase 9 reviews

4. **Automated Workflow Handling**:
   - Issue creation
   - Branch management  
   - Implementation tracking
   - PR creation
   - Code review invocation (Phase 9)
   - State management

**Only execute manual steps for**:
- Quick fixes that don't need full workflow
- Investigations or analysis
- Direct user requests for specific actions

**Before ANY development task, ask yourself**:
- Multiple related tasks? → Use OrchestratorAgent
- Single complex task? → Use WorkflowManager
- Need an issue/branch/PR? → Use agents, not manual execution

---

## Generic Claude Code Instructions

@claude-generic-instructions.md

## Project-Specific Instructions

@claude-project-specific.md
