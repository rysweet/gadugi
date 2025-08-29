# Complexity Analysis for Task Decomposition


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
Systematic approach to assessing task complexity to inform optimal decomposition strategies and resource allocation decisions.

## Complexity Dimensions

### 1. Technical Complexity
**Definition**: Difficulty of the technical solution required

**Low Complexity Indicators**:
- Single technology stack
- Well-established patterns
- Minimal external dependencies
- Clear solution path
- Existing similar implementations

**Medium Complexity Indicators**:
- Multiple technology components
- Some new or evolving technologies
- Moderate external dependencies
- Solution requires research/design
- Limited similar examples

**High Complexity Indicators**:
- Novel technical approaches required
- Multiple unknown technologies
- Complex external integrations
- Research and experimentation needed
- No existing reference implementations

**Impact on Decomposition**:
- Low: Standard patterns work well, predictable estimates
- Medium: Need buffer time, flexible subtasks
- High: Require spike/research phases, uncertain estimates

### 2. Domain Complexity
**Definition**: Complexity of the business domain or problem space

**Assessment Factors**:
- **Domain Knowledge Requirements**: How much specialized knowledge is needed?
- **Business Rule Complexity**: How many and how complex are the business rules?
- **Stakeholder Diversity**: How many different stakeholder perspectives must be considered?
- **Regulatory Requirements**: Are there compliance or regulatory constraints?

**Complexity Scoring**:
- **Low (1-3 points)**: Well-understood domain, simple rules, few stakeholders
- **Medium (4-7 points)**: Some domain expertise needed, moderate rules, multiple stakeholders
- **High (8-10 points)**: Deep domain expertise required, complex rules, many stakeholders

**Decomposition Impact**:
- High domain complexity requires more analysis and validation phases
- May need domain expert involvement in multiple subtasks
- Documentation becomes more critical for knowledge transfer

### 3. Integration Complexity
**Definition**: Complexity of integrating with existing systems and components

**Assessment Matrix**:

| Integration Points | Simple | Moderate | Complex |
|-------------------|--------|----------|---------|
| 0-1 systems       | Low    | Low      | Medium  |
| 2-3 systems       | Low    | Medium   | High    |
| 4+ systems        | Medium | High     | High    |

**Complexity Factors**:
- **API Maturity**: Well-documented vs. undocumented interfaces
- **Data Consistency**: Compatible vs. incompatible data models
- **Protocol Compatibility**: Standard vs. proprietary protocols
- **Error Handling**: Graceful vs. fragile error recovery
- **Testing Complexity**: Easy to mock vs. requires full integration

**Decomposition Strategies**:
- **Low**: Direct integration subtasks
- **Medium**: Add interface design and testing phases
- **High**: Create integration layer, extensive testing, fallback planning

### 4. Scale Complexity
**Definition**: Complexity introduced by performance, volume, or scale requirements

**Scale Indicators**:

**Volume Complexity**:
- Data volume: MB → GB → TB → PB
- Transaction volume: 10s → 100s → 1000s → 10000s per second
- User volume: 10s → 1000s → 100000s → millions

**Performance Complexity**:
- Response time requirements: seconds → milliseconds → microseconds
- Availability requirements: 99% → 99.9% → 99.99% → 99.999%
- Consistency requirements: eventual → strong → ACID

**Decomposition Adjustments**:
- **Low Scale**: Standard implementation patterns
- **Medium Scale**: Add performance testing, monitoring setup
- **High Scale**: Require architecture design, load testing, capacity planning phases

### 5. Change Complexity
**Definition**: How much existing code/systems must be modified

**Change Impact Assessment**:

**Low Impact (1-20% of codebase)**:
- New feature additions
- Configuration changes
- Documentation updates
- Minor bug fixes

**Medium Impact (20-50% of codebase)**:
- API modifications
- Database schema changes
- Workflow modifications
- Significant refactoring

**High Impact (>50% of codebase)**:
- Architecture changes
- Technology stack migrations
- Major system redesigns
- Cross-system modifications

**Risk Factors by Impact Level**:
- **Low**: Minimal risk, standard testing
- **Medium**: Regression risk, comprehensive testing needed
- **High**: System stability risk, phased rollout required

## Complexity Assessment Framework

### Step 1: Initial Complexity Scoring
For each task, score 1-10 on each dimension:

```
Technical Complexity:    [1-10]
Domain Complexity:       [1-10]
Integration Complexity:  [1-10]
Scale Complexity:        [1-10]
Change Complexity:       [1-10]
```

### Step 2: Weighted Complexity Score
Different task types have different complexity weights:

**Development Tasks**:
- Technical: 30%
- Domain: 20%
- Integration: 25%
- Scale: 15%
- Change: 10%

**Integration Tasks**:
- Technical: 20%
- Domain: 15%
- Integration: 40%
- Scale: 15%
- Change: 10%

**Refactoring Tasks**:
- Technical: 25%
- Domain: 10%
- Integration: 15%
- Scale: 20%
- Change: 30%

### Step 3: Risk Assessment
**Risk Multipliers**:
- New technology: +20%
- External dependencies: +15%
- Tight deadlines: +25%
- Distributed team: +10%
- Legacy systems: +20%

### Step 4: Complexity Classification
**Final Complexity Score**:
- **Low (1.0-3.5)**: Straightforward implementation
- **Medium (3.5-6.5)**: Requires careful planning
- **High (6.5-10.0)**: Needs extensive analysis and risk mitigation

## Decomposition Strategy by Complexity

### Low Complexity Tasks (1.0-3.5)
**Characteristics**:
- Predictable implementation
- Standard patterns apply
- Minimal unknowns
- Clear acceptance criteria

**Decomposition Approach**:
- Use proven templates
- Standard time estimates
- Minimal research phases
- Direct implementation path

**Example Subtasks**:
```
Analysis (20min) → Implementation (90min) → Testing (45min) → Review (30min)
                        ↓
                Documentation (30min)
```

**Success Factors**:
- Focus on execution efficiency
- Minimize overhead
- Standard quality gates

### Medium Complexity Tasks (3.5-6.5)
**Characteristics**:
- Some unknowns requiring investigation
- Multiple approaches possible
- Integration challenges likely
- Moderate risk of scope creep

**Decomposition Approach**:
- Add research/spike phases
- Include design validation
- Buffer estimates by 25-50%
- Plan for iteration

**Example Subtasks**:
```
Analysis (45min) → Research Spike (60min) → Design (60min) → Prototype (90min)
                                                ↓                ↓
                                    Implementation (120min) → Testing (90min)
                                                ↓                ↓
                                    Integration (60min) → Validation (45min)
                                                ↓
                                    Documentation (45min)
```

**Success Factors**:
- Front-load investigation work
- Plan for design iterations
- Include validation checkpoints

### High Complexity Tasks (6.5-10.0)
**Characteristics**:
- Significant unknowns
- Novel approaches required
- High integration complexity
- Multiple failure modes possible

**Decomposition Approach**:
- Extensive research and analysis phases
- Proof-of-concept development
- Risk mitigation strategies
- Phased implementation
- Buffer estimates by 100%+

**Example Subtasks**:
```
Domain Analysis (90min) → Technical Research (120min) → Architecture Design (180min)
              ↓                      ↓                           ↓
    Stakeholder Review (60min) → Proof of Concept (240min) → Design Review (90min)
              ↓                      ↓                           ↓
    Phase 1 Implementation (180min) → Integration Testing (120min) → Risk Assessment (60min)
              ↓                      ↓                           ↓
    Phase 2 Implementation (180min) → System Testing (180min) → Performance Validation (120min)
              ↓                      ↓                           ↓
    Documentation (90min) ← Security Review (90min) ← Production Readiness (90min)
```

**Success Factors**:
- Reduce unknowns early through research
- Validate assumptions with prototypes
- Plan multiple implementation phases
- Include extensive quality gates

## Complexity Indicators by Task Type

### Feature Development
**Low**: Simple CRUD operations, UI forms, basic reporting
**Medium**: Workflow implementations, API integrations, data transformations
**High**: Real-time systems, AI/ML features, complex business logic

### Bug Fixes
**Low**: Configuration issues, simple logic errors, UI fixes
**Medium**: Integration issues, performance problems, data consistency
**High**: Race conditions, memory leaks, distributed system bugs

### Refactoring
**Low**: Code cleanup, variable renaming, simple pattern application
**Medium**: Module restructuring, database schema changes, API modifications
**High**: Architecture changes, technology migrations, system redesigns

### Infrastructure
**Low**: Configuration updates, monitoring setup, simple deployments
**Medium**: CI/CD pipeline changes, load balancer setup, database scaling
**High**: Multi-region deployments, disaster recovery, major platform migrations

## Adaptive Complexity Assessment

### Learning from Historical Data
**Track Complexity Prediction Accuracy**:
- Compare initial complexity assessment with actual difficulty
- Identify consistently under-estimated complexity types
- Refine assessment criteria based on outcomes

**Pattern Recognition**:
- Similar tasks with similar complexity should have similar outcomes
- Identify complexity patterns that lead to success or failure
- Build complexity pattern library over time

### Team-Specific Adjustments
**Capability Assessment**:
- Team experience with technology reduces technical complexity
- Domain expertise reduces domain complexity
- Integration experience reduces integration complexity

**Adjustment Factors**:
- **Expert Team**: Reduce complexity score by 15-25%
- **Experienced Team**: Reduce complexity score by 10-15%
- **Novice Team**: Increase complexity score by 20-30%

### Context-Specific Factors
**Time Pressure**: +20-50% complexity (less time for careful analysis)
**Quality Requirements**: +10-30% complexity (more validation needed)
**External Dependencies**: +15-25% complexity (less control over timeline)
**Legacy Systems**: +20-40% complexity (undocumented behavior, technical debt)

## Complexity Monitoring and Adjustment

### During Task Execution
**Early Warning Signs**:
- Subtasks taking >150% of estimated time
- Unexpected technical roadblocks
- Requirements clarification needs
- Integration difficulties

**Adaptation Strategies**:
- Re-assess complexity mid-task
- Adjust remaining subtask estimates
- Add additional quality gates if needed
- Consider scope reduction if timeline is fixed

### Post-Task Learning
**Complexity Accuracy Metrics**:
- Actual vs. predicted complexity score
- Estimate accuracy by complexity level
- Success rate by complexity category
- Common complexity blind spots

**Continuous Improvement**:
- Refine complexity assessment criteria
- Update decomposition templates
- Improve team capability assessment
- Build better estimation models
