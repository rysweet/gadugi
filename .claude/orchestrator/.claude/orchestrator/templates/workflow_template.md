# WorkflowManager Task Template

This is a template for generating WorkflowManager tasks.

## Variables Available:
- {task_id}: Unique task identifier
- {task_name}: Human-readable task name
- {original_prompt}: Path to the original prompt file
- {requirements}: Extracted requirements section
- {technical_analysis}: Extracted technical analysis
- {implementation_plan}: Extracted implementation plan
- {success_criteria}: Extracted success criteria

## Usage:
This template is used by PromptGenerator to create context-aware prompts
for WorkflowManager execution in parallel worktree environments.
