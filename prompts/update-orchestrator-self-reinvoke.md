# Update Orchestrator Agent for Flexible Input Processing

## Task
Update the orchestrator agent to handle any type of input (not just existing prompt files) by automatically creating prompt files for task descriptions before executing them.

## Requirements

1. **Update `.claude/agents/orchestrator-agent.md`**:
   - Add input processing logic to handle both prompt files and task descriptions
   - Check if input refers to existing prompt files or is a task description
   - For task descriptions, invoke prompt-writer to create structured prompt files
   - Process all inputs into a list of executable prompt files

2. **Input Processing Pattern**:
   Add input validation and processing logic:
   ```markdown
   ## Input Processing and Prompt File Creation

   The orchestrator must handle ANY type of input:

   1. Check if input is an existing prompt file
   2. If not, treat it as a task description:
      - Invoke prompt-writer agent to create prompt file
      - Save to prompts/ directory
      - Add to execution list
   3. Continue with normal orchestration workflow
   ```

3. **Processing Flow**:
   - Accept mixed inputs (files and descriptions)
   - Transform all inputs into prompt files
   - Maintain execution list consistency
   - Enable flexible user interaction

4. **Benefits**:
   - Users can provide task descriptions directly
   - No need to manually create prompt files first
   - More intuitive orchestrator usage
   - Maintains structured workflow process

5. **Test scenarios**:
   - Input: "Fix bug in login system" → Creates prompt file
   - Input: "existing-prompt.md" → Uses existing file
   - Input: Mixed list → Processes each appropriately

## Implementation Notes

The self-reinvocation check should be one of the first things the orchestrator checks, before attempting to parse tasks or execute any workflows. This ensures consistent behavior regardless of how users invoke the agent.

## Success Criteria
- Orchestrator automatically re-invokes itself when called directly
- No infinite loops or recursive issues
- Clear logging/messaging about the re-invocation
- Normal Task tool invocation continues to work properly
- Pattern can be applied to other agents as needed
