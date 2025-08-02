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
   /agent:workflow-master
   
   Task: Execute workflow for /prompts/[prompt-file].md
   ```

3. **Agent Hierarchy**:
   - **OrchestratorAgent**: Top-level coordinator for parallel execution
   - **WorkflowMaster**: Handles individual workflow execution
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
- Single complex task? → Use WorkflowMaster
- Need an issue/branch/PR? → Use agents, not manual execution

---

## Generic Claude Code Instructions

@claude-generic-instructions.md

## Project-Specific Instructions

@claude-project-specific.md

## Communication Guidelines

### Language Style
- Use neutral, factual language in all communications
- Focus on functionality and features, not superlatives
- Avoid self-congratulatory or promotional language

### Specific Terms to Avoid
- "major accomplishment" → "completed task"
- "enterprise-grade" → "scalable" 
- "production-ready" → "tested"
- "significant enhancement" → "improvement"
- "comprehensive" → "complete"
- "robust" → "reliable"
- "excellent/exceptional" → "good"
- "cutting-edge" → "current"
- "groundbreaking" → "new"

### PR and Issue Descriptions
- State what was done, not how well it was done
- List features and changes factually
- Describe functionality without adjectives
- Focus on user value, not technical impressiveness

### Code Review Comments
- "The implementation works correctly" instead of "Excellent implementation"
- "This follows project conventions" instead of "Outstanding code quality"
- Point out issues directly without cushioning language
- Suggest improvements without excessive praise
