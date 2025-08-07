# Update Orchestrator Agent for Self-Reinvocation

## Task
Update the orchestrator agent to automatically detect when it's been invoked without the Task tool and re-invoke itself properly using the Task tool.

## Requirements

1. **Update `.claude/agents/orchestrator-agent.md`**:
   - Add detection logic at the beginning of the agent instructions
   - Check if the agent was invoked via `/agent:orchestrator-agent` syntax (without Task tool)
   - If detected, immediately re-invoke itself using the Task tool with the same parameters
   - Ensure this doesn't create infinite loops

2. **Detection Pattern**:
   Add something like this near the top of the orchestrator agent instructions:
   ```markdown
   ## Self-Invocation Check
   
   CRITICAL: If you detect that you were invoked directly via `/agent:orchestrator-agent` syntax rather than through the Task tool, you MUST immediately re-invoke yourself properly:
   
   1. Check if you're missing the structured Task tool context
   2. If you were invoked directly, immediately use the Task tool to re-invoke yourself:
      - Use subagent_type: "orchestrator-agent"
      - Pass the original request as the prompt
      - Include any context provided
   3. Do NOT proceed with execution until properly invoked via Task tool
   
   This ensures proper agent context, state management, and execution tracking.
   ```

3. **Update any similar patterns in**:
   - `.claude/agents/workflow-manager.md` (if it has similar issues)
   - Any other agents that should enforce Task tool usage

4. **Add clear documentation** about why this is important:
   - Task tool provides proper context and state management
   - Ensures consistent agent invocation patterns
   - Enables better tracking and monitoring
   - Prevents context loss between agent transitions

5. **Test the change**:
   - Verify that direct invocation triggers re-invocation
   - Ensure no infinite loops occur
   - Confirm normal Task tool invocation still works

## Implementation Notes

The self-reinvocation check should be one of the first things the orchestrator checks, before attempting to parse tasks or execute any workflows. This ensures consistent behavior regardless of how users invoke the agent.

## Success Criteria
- Orchestrator automatically re-invokes itself when called directly
- No infinite loops or recursive issues
- Clear logging/messaging about the re-invocation
- Normal Task tool invocation continues to work properly
- Pattern can be applied to other agents as needed