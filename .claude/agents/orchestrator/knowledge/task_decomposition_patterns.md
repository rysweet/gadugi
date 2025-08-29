# Task Decomposition Patterns


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Overview

This document captures learned patterns for intelligent task decomposition in the Orchestrator V0.3. These patterns are used to automatically break down complex tasks into optimally parallelizable subtasks.

## Core Decomposition Strategies

### 1. Feature Implementation Pattern

**Triggers**: "implement", "add feature", "create functionality", "build component"

**Optimal Subtasks**:
1. **Architecture Design** (120-300s, 90% success)
   - Analyze requirements and design system architecture
   - Define interfaces and data models
   - Plan integration points

2. **Core Implementation** (300-900s, 75% success)
   - Implement main business logic
   - Create data access layer
   - Build core functionality

3. **Testing Suite** (180-450s, 85% success, parallel with docs)
   - Unit tests for core logic
   - Integration tests
   - Edge case validation

4. **Documentation** (90-180s, 95% success, parallel with tests)
   - API documentation
   - User guides
   - Code comments

5. **Integration Testing** (120-300s, 80% success)
   - End-to-end testing
   - Performance validation
   - Cross-system compatibility

**Dependencies**:
- Core Implementation depends on Architecture Design
- Testing Suite can start after Core Implementation begins (50% complete)
- Integration Testing depends on Core Implementation + Testing Suite
- Documentation can run parallel with Testing Suite

**Success Rate**: 82%
**Average Speedup**: 2.3x

### 2. Bug Fix Pattern

**Triggers**: "fix bug", "resolve issue", "error", "problem", "broken"

**Optimal Subtasks**:
1. **Root Cause Analysis** (120-360s, 85% success)
   - Reproduce the bug
   - Analyze error logs
   - Identify root cause

2. **Impact Assessment** (60-120s, 90% success, parallel with analysis)
   - Assess affected components
   - Evaluate severity
   - Plan rollback strategy

3. **Fix Implementation** (180-480s, 90% success)
   - Implement the fix
   - Add regression tests
   - Validate fix locally

4. **Verification Testing** (90-180s, 95% success)
   - Run all tests
   - Verify fix works
   - Check for side effects

**Dependencies**:
- Fix Implementation depends on Root Cause Analysis
- Impact Assessment can run parallel with Root Cause Analysis
- Verification Testing depends on Fix Implementation

**Success Rate**: 90%
**Average Speedup**: 1.8x

### 3. Testing Workflow Pattern

**Triggers**: "test", "testing", "validate", "verification", "quality assurance"

**Optimal Subtasks**:
1. **Test Planning** (90-180s, 95% success)
   - Analyze test requirements
   - Create test strategy
   - Identify test data needs

2. **Unit Test Implementation** (180-360s, 85% success, parallel)
   - Create unit tests
   - Test individual components
   - Mock external dependencies

3. **Integration Test Implementation** (240-480s, 80% success, parallel)
   - Create integration tests
   - Test component interactions
   - Validate data flow

4. **End-to-End Test Implementation** (300-600s, 75% success)
   - Create E2E test scenarios
   - Test complete user workflows
   - Validate system behavior

5. **Test Execution and Reporting** (120-300s, 90% success)
   - Run all test suites
   - Generate test reports
   - Analyze coverage

**Dependencies**:
- Unit and Integration tests can run parallel after Test Planning
- E2E tests can start after Integration tests are 50% complete
- Test Execution depends on all test implementations

**Success Rate**: 85%
**Average Speedup**: 2.5x

### 4. Refactoring Pattern

**Triggers**: "refactor", "restructure", "reorganize", "clean up", "improve code"

**Optimal Subtasks**:
1. **Code Analysis** (120-240s, 95% success)
   - Analyze current code structure
   - Identify refactoring opportunities
   - Assess technical debt

2. **Safety Net Creation** (180-300s, 90% success)
   - Create comprehensive tests
   - Document current behavior
   - Set up monitoring

3. **Refactoring Plan** (90-150s, 95% success)
   - Create step-by-step plan
   - Identify breaking changes
   - Plan rollback strategy

4. **Incremental Refactoring** (360-720s, 80% success)
   - Execute refactoring in small steps
   - Validate after each step
   - Maintain functionality

5. **Validation and Cleanup** (120-240s, 90% success)
   - Run all tests
   - Validate performance
   - Clean up temporary code

**Dependencies**:
- Safety Net Creation can start parallel with Code Analysis
- Refactoring Plan depends on Code Analysis
- Incremental Refactoring depends on Safety Net + Plan
- Validation depends on Incremental Refactoring

**Success Rate**: 88%
**Average Speedup**: 2.0x

### 5. Documentation Pattern

**Triggers**: "document", "documentation", "readme", "docs", "guide"

**Optimal Subtasks**:
1. **Content Planning** (60-120s, 95% success)
   - Define documentation scope
   - Create content outline
   - Identify audience

2. **API Documentation** (120-240s, 85% success, parallel)
   - Document public APIs
   - Create usage examples
   - Document parameters

3. **User Guide Creation** (180-360s, 80% success, parallel)
   - Write user-facing documentation
   - Create tutorials
   - Add troubleshooting guides

4. **Developer Documentation** (120-240s, 85% success, parallel)
   - Document architecture
   - Write contribution guidelines
   - Add setup instructions

5. **Review and Publishing** (60-120s, 90% success)
   - Review all documentation
   - Check formatting
   - Publish to appropriate channels

**Dependencies**:
- API, User Guide, and Developer docs can run parallel after Content Planning
- Review and Publishing depends on all documentation tasks

**Success Rate**: 87%
**Average Speedup**: 2.8x

## Advanced Patterns

### 6. Multi-Service Integration Pattern

**Triggers**: "integrate", "connect services", "API integration", "system integration"

**Optimal Subtasks**:
1. **Integration Analysis** (180-300s, 85% success)
2. **Service A Integration** (240-480s, 75% success, parallel)
3. **Service B Integration** (240-480s, 75% success, parallel)
4. **Cross-Service Testing** (180-360s, 80% success)
5. **Integration Documentation** (120-180s, 90% success, parallel)

**Dependencies**: Cross-Service Testing depends on both service integrations

### 7. Performance Optimization Pattern

**Triggers**: "optimize", "performance", "speed up", "improve efficiency"

**Optimal Subtasks**:
1. **Performance Profiling** (120-240s, 90% success)
2. **Bottleneck Identification** (90-180s, 85% success)
3. **Algorithm Optimization** (240-600s, 70% success, parallel)
4. **Database Optimization** (180-360s, 75% success, parallel)
5. **Caching Implementation** (120-240s, 80% success, parallel)
6. **Performance Validation** (90-180s, 85% success)

### 8. Security Implementation Pattern

**Triggers**: "security", "authentication", "authorization", "secure"

**Optimal Subtasks**:
1. **Security Requirements Analysis** (120-180s, 90% success)
2. **Authentication Implementation** (240-480s, 80% success)
3. **Authorization Implementation** (180-360s, 75% success)
4. **Security Testing** (180-300s, 85% success)
5. **Security Documentation** (90-150s, 90% success, parallel)

## Pattern Selection Algorithm

### 1. Keyword-Based Matching
- Extract keywords from task description
- Match against pattern trigger words
- Calculate keyword overlap score

### 2. Context Analysis
- Consider project type and technology stack
- Analyze similar past tasks
- Factor in team expertise areas

### 3. Confidence Scoring
```python
confidence_score = (
    keyword_match_score * 0.4 +
    context_similarity_score * 0.3 +
    historical_success_rate * 0.3
)
```

### 4. Pattern Adaptation Rules
- If confidence < 0.6: Use generic decomposition
- If confidence 0.6-0.8: Adapt pattern with modifications
- If confidence > 0.8: Use pattern as-is

## Learning and Adaptation

### Success Rate Tracking
- Track pattern success rates over time
- Adjust timing estimates based on actual performance
- Update dependencies based on observed bottlenecks

### Pattern Evolution
- Create new patterns from successful novel decompositions
- Merge similar patterns that show consistent success
- Retire patterns with consistently low success rates

### Context-Specific Adaptations
- Adjust patterns based on team size and expertise
- Modify for different technology stacks
- Adapt for project complexity and constraints

## Quality Metrics

### Pattern Effectiveness Metrics
- **Success Rate**: Percentage of tasks completed successfully
- **Time Accuracy**: How close predictions are to actual execution time
- **Speedup Factor**: Sequential time / parallel time
- **Resource Utilization**: How efficiently resources are used

### Target Thresholds
- Success Rate: > 80%
- Time Accuracy: > 70%
- Speedup Factor: > 2.0x for patterns with 3+ parallel tasks
- Resource Utilization: > 75%

### Pattern Retirement Criteria
- Success rate drops below 60% for 10+ executions
- Average speedup falls below 1.5x
- Pattern becomes obsolete due to technology changes

## Best Practices

### Pattern Design Principles
1. **Granular Tasks**: Each subtask should be 2-10 minutes of focused work
2. **Clear Dependencies**: Dependencies should be explicit and minimal
3. **Parallel Opportunities**: Identify tasks that can run simultaneously
4. **Failure Isolation**: Design so failures don't cascade
5. **Resource Balance**: Mix CPU, I/O, and memory intensive tasks

### Common Anti-Patterns to Avoid
1. **Over-Decomposition**: Creating too many tiny tasks (overhead dominates)
2. **Under-Decomposition**: Creating tasks that are too large (poor parallelism)
3. **Tight Coupling**: Tasks that depend heavily on each other
4. **Resource Conflicts**: Multiple tasks competing for same resources
5. **Critical Path Ignorance**: Not optimizing the longest dependency chain

## Pattern Templates

### Generic Task Template
```yaml
pattern_name: "Generic Task Pattern"
triggers: ["general", "misc", "other"]
subtasks:
  - name: "Analysis"
    duration_range: [60, 180]
    success_rate: 0.90
    dependencies: []
  - name: "Implementation"
    duration_range: [180, 600]
    success_rate: 0.75
    dependencies: ["Analysis"]
  - name: "Validation"
    duration_range: [90, 180]
    success_rate: 0.85
    dependencies: ["Implementation"]
```

This knowledge base is continuously updated based on execution results and learning outcomes.
