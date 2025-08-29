# Rename All Agents from kebab-case to CamelCase

## Objective
Rename all agent files from kebab-case to CamelCase format and update all references throughout the codebase.

## Requirements

1. **Research Phase**:
   - Find all agent files with kebab-case names
   - Identify all references to these agents in the codebase
   - Map out the renaming strategy
   - Check for backward compatibility requirements

2. **Implementation Phase**:
   - Rename agent files to CamelCase (e.g., `code-reviewer.md` → `CodeReviewer.md`)
   - Update all agent invocation references
   - Update documentation references
   - Maintain backward compatibility where needed
   - Update agent registry/manifests

3. **Testing Phase**:
   - Verify all agents are accessible with new names
   - Test agent invocations work correctly
   - Validate no broken references remain
   - Test backward compatibility if implemented
   - Run full test suite

## Technical Details

### Agent Locations
- Main agents: `.claude/agents/`
- Prompt files: `prompts/`
- Documentation: `docs/agents/`

### Renaming Mapping Examples
- `code-reviewer.md` → `CodeReviewer.md`
- `workflow-manager.md` → `WorkflowManager.md`
- `task-analyzer.md` → `TaskAnalyzer.md`
- `prompt-writer.md` → `PromptWriter.md`
- `orchestrator-agent.md` → `OrchestratorAgent.md`

### Reference Update Locations
1. Agent invocation strings (`/agent:code-reviewer` → `/agent:CodeReviewer`)
2. Documentation files
3. Test files
4. Configuration files
5. Scripts and automation

## Success Criteria
- [ ] All agent files renamed to CamelCase
- [ ] All references updated throughout codebase
- [ ] No broken agent invocations
- [ ] Backward compatibility maintained (if needed)
- [ ] Documentation updated
- [ ] Tests passing

## Testing Requirements
- Agent invocation tests
- Reference integrity tests
- Backward compatibility tests
- Integration tests
- Documentation validation

## Documentation Updates
- Agent naming conventions guide
- Migration guide for users
- Updated agent documentation
- Reference guide updates