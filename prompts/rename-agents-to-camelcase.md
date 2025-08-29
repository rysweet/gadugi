# Rename All Agents from kebab-case to CamelCase

## Objective
Rename all agent files in `.claude/agents/` from kebab-case to CamelCase format to maintain consistency and professionalism.

## Priority
HIGH

## Tasks

### 1. Rename Agent Files
Convert all kebab-case agent filenames to CamelCase:

**Files to rename:**
- AgentUpdater.md → AgentUpdater.md
- ClaudeSettingsUpdate.md → ClaudeSettingsUpdate.md
- CodeExecutor.md → CodeExecutor.md
- CodeReviewResponse.md → CodeReviewResponse.md
- CodeReviewer.md → CodeReviewer.md
- EventRouterManager.md → EventRouterManager.md
- EventRouterServiceManager.md → EventRouterServiceManager.md
- ExecutionMonitor.md → ExecutionMonitor.md
- GadugiCoordinator.md → GadugiCoordinator.md
- GitHubExecutor.md → GitHubExecutor.md
- LlmProxyAgent.md → LlmProxyAgent.md
- MemoryManager.md → MemoryManager.md
- MemoryServiceManager.md → MemoryServiceManager.md
- Neo4jServiceManager.md → Neo4jServiceManager.md
- OrchestratorAgent.md → OrchestratorAgent.md
- PrBacklogManager.md → PrBacklogManager.md
- ProgramManager.md → ProgramManager.md
- PromptWriter.md → PromptWriter.md
- ReadmeAgent.md → ReadmeAgent.md
- RecipeExecutor.md → RecipeExecutor.md
- SystemDesignReviewer.md → SystemDesignReviewer.md
- TaskAnalyzer.md → TaskAnalyzer.md
- TaskBoundsEval.md → TaskBoundsEval.md
- TaskDecomposer.md → TaskDecomposer.md
- TaskResearchAgent.md → TaskResearchAgent.md
- TeamCoach.md → TeamCoach.md
- TeamcoachAgent.md → TeamcoachAgent.md
- TestExecutor.md → TestExecutor.md
- TestSolver.md → TestSolver.md
- TestWriter.md → TestWriter.md
- TypeFixAgent.md → TypeFixAgent.md
- WorkflowManagerPhase9Enforcement.md → WorkflowManagerPhase9Enforcement.md
- WorkflowManagerSimplified.md → WorkflowManagerSimplified.md
- WorkflowManager.md → WorkflowManager.md
- WorkflowPhaseReflection.md → WorkflowPhaseReflection.md
- WorktreeExecutor.md → WorktreeExecutor.md
- WorktreeManager.md → WorktreeManager.md
- XpiaDefenseAgent.md → XpiaDefenseAgent.md

### 2. Update All References
After renaming files, update all references throughout the codebase:

**Locations to check and update:**
- Task tool invocations in all Python files
- Agent invocations in prompts/ directory
- Documentation files (*.md) 
- Scripts in scripts/ directory
- Test files referencing agents
- The orchestrator implementation
- Any configuration files
- CLAUDE.md and other instruction files

### 3. Create Compatibility Layer (Optional)
Consider creating symlinks or aliases for backward compatibility during transition:
- Create symlinks from old names to new names
- Add deprecation notices
- Plan removal of symlinks in future version

### 4. Validation
- Verify all agent files are renamed correctly
- Ensure no broken references remain
- Test agent invocations still work
- Run integration tests to verify functionality

## Success Criteria
- All agent files follow CamelCase naming convention
- No broken references in the codebase
- All tests pass
- Agent invocations work correctly with new names