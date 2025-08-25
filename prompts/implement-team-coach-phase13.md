# Implement Team Coach as Phase 13 in Workflow

## Objective
Integrate the Team Coach agent as Phase 13 (Team Coach Reflection) - a mandatory session-ending phase that automatically analyzes completed workflows and generates improvement recommendations.

## Context
The Team Coach agent is already implemented and functional. We need to integrate it as the final phase of every workflow to ensure continuous improvement and learning from each development session.

## Requirements

### 1. Update CLAUDE.md
Add Phase 13 to the mandatory 11-phase workflow (making it 12 phases total):
- Phase 13: Team Coach Reflection (MANDATORY - session end)
- This phase must execute after Phase 12 (Settings Update)
- Must be clearly marked as mandatory for all workflows
- Should include description of what Team Coach does in this phase

### 2. Update workflow-manager.md  
Modify the WorkflowManager agent to:
- Add Phase 13 execution logic after Phase 12
- Ensure Team Coach is invoked safely without subprocess spawning
- Use direct function calls or agent invocation patterns
- Save Team Coach insights to Memory.md
- Include proper error handling with graceful degradation
- Record Phase 13 completion in workflow state

### 3. Update orchestrator-agent.md
Enhance the OrchestratorAgent to:
- Recognize Phase 13 as part of the complete workflow
- Validate Phase 13 completion in post-task analysis
- Aggregate Team Coach insights from parallel workflows
- Generate consolidated improvement recommendations
- Update Memory.md with aggregated insights

### 4. Implementation Details

#### Phase 13 Execution Flow:
1. Workflow completes Phase 12 (Settings Update)
2. WorkflowManager invokes Team Coach agent
3. Team Coach analyzes the completed session:
   - Performance metrics from all phases
   - Success/failure patterns
   - Time spent on each phase
   - Quality of outputs
4. Team Coach generates recommendations:
   - Process improvements
   - Tool optimizations
   - Workflow enhancements
   - Agent coordination improvements
5. Insights are saved to Memory.md:
   - Session summary
   - Key learnings
   - Improvement recommendations
   - Metrics for tracking
6. Optional: Create GitHub issues for significant improvements
7. Phase 13 marked as complete

#### Safety Requirements:
- NO subprocess spawning - use direct invocation
- Timeout protection (max 2 minutes for analysis)
- Graceful degradation if Team Coach fails
- Must not block workflow completion
- Must not create infinite loops

## Testing Requirements

### Test Scenarios:
1. Simple workflow with all phases completing successfully
2. Workflow with some phase failures to test error handling
3. Parallel workflows to test aggregation
4. Team Coach timeout scenario
5. Team Coach failure scenario (graceful degradation)

### Success Criteria:
- Team Coach is invoked automatically at session end
- Insights are successfully saved to Memory.md
- No infinite process spawning occurs
- Workflow completes even if Team Coach fails
- Performance impact is minimal (< 30 seconds added)

## Expected Outcomes
1. Every workflow session ends with Team Coach analysis
2. Continuous improvement insights are captured automatically
3. Memory.md contains actionable recommendations
4. Development team benefits from automated coaching
5. No manual invocation of Team Coach needed

## Implementation Priority
HIGH - This enhancement will provide immediate value by:
- Automating performance analysis
- Capturing learnings from every session
- Building a knowledge base of improvements
- Reducing manual review overhead