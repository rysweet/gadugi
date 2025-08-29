# Task Patterns and Optimal Decompositions

## Overview
Common task types encountered in software development and their optimal decomposition patterns based on learned experiences and proven practices.

## Primary Task Patterns

### 1. New Feature Development
**Recognition Patterns**:
- `implement new`, `create feature`, `build component`, `develop functionality`
- `add capability`, `new module`, `feature request`

**Optimal Decomposition**:
```
Analysis (30min) → Design (60min) → Implementation (180min)
                     ↓                    ↓
                Documentation (45min) ← Testing (90min)
                     ↓
                Review (30min)
```

**Parallelization Score**: 0.65
**Critical Path**: Analysis → Design → Implementation → Testing → Review
**Parallel Opportunities**: Documentation can start after Design

**Success Factors**:
- Clear requirements gathering reduces rework
- Early documentation prevents knowledge gaps
- Parallel testing preparation improves efficiency

### 2. Bug Resolution
**Recognition Patterns**:
- `fix bug`, `resolve issue`, `patch`, `debug problem`
- `error in`, `not working`, `broken`, `failing`

**Optimal Decomposition**:
```
Reproduction (15min) → Analysis (45min) → Fix (90min) → Testing (60min) → Verification (30min)
                                            ↓
                                    Documentation (20min)
```

**Parallelization Score**: 0.25
**Critical Path**: Reproduction → Analysis → Fix → Testing → Verification
**Parallel Opportunities**: Limited to documentation phase

**Success Factors**:
- Accurate reproduction is critical for effective analysis
- Thorough testing prevents regression issues
- Quick documentation ensures knowledge retention

### 3. Code Refactoring
**Recognition Patterns**:
- `refactor`, `restructure`, `clean up code`, `improve structure`
- `optimize`, `modernize`, `technical debt`

**Optimal Decomposition**:
```
Code Analysis (45min) → Planning (30min) → Refactor Module A (90min)
                                      ↓         ↓
                                Refactor Module B (90min) → Integration (30min)
                                      ↓         ↓              ↓
                              Testing (60min) ←←←←←←← Performance Check (45min)
                                      ↓
                              Documentation (30min)
```

**Parallelization Score**: 0.70
**Critical Path**: Analysis → Planning → Integration → Testing
**Parallel Opportunities**: Multiple modules can be refactored simultaneously

**Success Factors**:
- Modular approach enables parallelization
- Comprehensive testing prevents functionality loss
- Performance validation ensures improvements

### 4. API Development
**Recognition Patterns**:
- `create API`, `build endpoint`, `REST service`, `GraphQL`
- `microservice`, `web service`, `API implementation`

**Optimal Decomposition**:
```
API Design (60min) → Schema Definition (30min) → Implementation (120min)
        ↓                    ↓                         ↓
Documentation (45min) ← Test Cases (60min) ← Integration Tests (75min)
        ↓                    ↓                         ↓
    Validation (30min) ← Unit Tests (45min) ← Performance Tests (60min)
```

**Parallelization Score**: 0.75
**Critical Path**: Design → Implementation → Integration Tests
**Parallel Opportunities**: Documentation, test case creation, different test types

**Success Factors**:
- Clear API design prevents implementation issues
- Parallel test development improves coverage
- Early documentation aids client integration

### 5. Database Operations
**Recognition Patterns**:
- `database`, `schema`, `migration`, `data model`
- `SQL`, `query optimization`, `index`, `backup`

**Optimal Decomposition**:
```
Schema Design (45min) → Migration Script (60min) → Data Migration (90min)
        ↓                      ↓                         ↓
Index Planning (30min) → Index Creation (30min) → Performance Test (60min)
        ↓                      ↓                         ↓
Documentation (30min) ← Testing (45min) ←←←← Backup Verification (30min)
```

**Parallelization Score**: 0.60
**Critical Path**: Schema → Migration Script → Data Migration → Performance Test
**Parallel Opportunities**: Index work can be parallel to migration development

**Success Factors**:
- Careful schema design prevents costly migrations
- Parallel index optimization reduces downtime
- Comprehensive testing ensures data integrity

### 6. UI/Frontend Development
**Recognition Patterns**:
- `user interface`, `frontend`, `UI component`, `web page`
- `React`, `Angular`, `Vue`, `styling`, `responsive`

**Optimal Decomposition**:
```
Design Review (30min) → Component Structure (45min) → Component A (60min)
                              ↓                         ↓
                      Component B (60min) → Styling (45min) → Integration (30min)
                              ↓                         ↓              ↓
                      Component C (60min) → Testing (60min) → Review (30min)
                              ↓                         ↓
                      Documentation (30min) ← Accessibility (45min)
```

**Parallelization Score**: 0.80
**Critical Path**: Design → Structure → Integration → Review
**Parallel Opportunities**: Independent components, styling, testing, documentation

**Success Factors**:
- Component isolation enables high parallelization
- Early styling work prevents integration issues
- Accessibility considerations prevent rework

### 7. Testing Suite Development
**Recognition Patterns**:
- `test suite`, `automated testing`, `QA`, `test coverage`
- `unit tests`, `integration tests`, `E2E tests`

**Optimal Decomposition**:
```
Test Planning (30min) → Test Case Design (45min) → Unit Tests (60min)
                              ↓                         ↓
                      Integration Tests (75min) → E2E Tests (90min)
                              ↓                         ↓
                      Performance Tests (60min) → Test Automation (45min)
                              ↓                         ↓
                      Reporting Setup (30min) ← Documentation (30min)
```

**Parallelization Score**: 0.85
**Critical Path**: Planning → Design → Test Automation
**Parallel Opportunities**: Different test types can be developed simultaneously

**Success Factors**:
- Clear test planning enables parallel development
- Independent test types maximize parallelization
- Early automation setup improves efficiency

## Secondary Task Patterns

### 8. Performance Optimization
**Recognition Patterns**: `optimize performance`, `improve speed`, `reduce latency`
**Parallelization Score**: 0.65
**Key Strategy**: Profile first, then parallelize optimization efforts

### 9. Security Implementation
**Recognition Patterns**: `security`, `authentication`, `authorization`, `encryption`
**Parallelization Score**: 0.45
**Key Strategy**: Security review gates limit parallelization but ensure quality

### 10. DevOps/Infrastructure
**Recognition Patterns**: `deploy`, `CI/CD`, `infrastructure`, `Docker`, `Kubernetes`
**Parallelization Score**: 0.55
**Key Strategy**: Environment setup can be parallelized but deployment is sequential

### 11. Documentation Creation
**Recognition Patterns**: `documentation`, `README`, `user guide`, `API docs`
**Parallelization Score**: 0.90
**Key Strategy**: Highest parallelization potential - different sections independent

### 12. Data Processing
**Recognition Patterns**: `data processing`, `ETL`, `data pipeline`, `analytics`
**Parallelization Score**: 0.70
**Key Strategy**: Data dependencies create some sequencing but processing can be parallel

## Pattern Combinations

### Complex Feature (Multiple Patterns)
When tasks combine multiple patterns (e.g., "Implement user authentication with database and API"):

1. **Decompose by Pattern**: Separate database, API, and security concerns
2. **Identify Interfaces**: Define clear boundaries between pattern implementations
3. **Sequence Dependencies**: API depends on database, security integrates with both
4. **Maximize Parallelism**: Different teams can work on different patterns

### Migration Projects
Pattern combination of refactoring + new implementation:

1. **Phase Approach**: Old system analysis → New system design → Migration execution
2. **Dual Track**: Maintain old system while building new (parallel)
3. **Integration Points**: Define and implement interfaces early
4. **Testing Strategy**: Parallel test development for both systems

## Anti-Patterns to Avoid

### 1. Over-Decomposition
**Problem**: Breaking tasks too small creates coordination overhead
**Solution**: Maintain 30-180 minute subtask sizes for optimal parallelization

### 2. Under-Decomposition
**Problem**: Large tasks prevent parallelization and create bottlenecks
**Solution**: Break any task >4 hours into smaller components

### 3. Dependency Chains
**Problem**: Long sequential chains eliminate parallelization benefits
**Solution**: Look for opportunities to break dependencies or create parallel paths

### 4. Resource Conflicts
**Problem**: Multiple subtasks competing for same resources
**Solution**: Consider resource constraints in decomposition strategy

## Learning Indicators

### High Success Patterns
- Clear separation of concerns
- Well-defined interfaces between subtasks
- Appropriate granularity (30-180 min per subtask)
- Minimal critical path dependencies

### Optimization Opportunities
- Tasks with low parallelization achievement vs. prediction
- Frequent bottlenecks in similar task types
- Consistent time overruns in specific patterns
- Resource contention issues

### Pattern Evolution
- New task patterns emerge from changing technology stacks
- Successful adaptations become new standard patterns
- Failed experiments inform anti-pattern identification
- Team capabilities influence optimal decomposition strategies

## Context Considerations

### Team Size Impact
- **Small Teams (1-3)**: Focus on clear sequencing, minimal coordination overhead
- **Medium Teams (4-7)**: Balance parallelization with communication needs
- **Large Teams (8+)**: Maximize parallelization, invest in coordination tools

### Technology Stack Influence
- **Monolithic Systems**: More sequential dependencies
- **Microservices**: Higher parallelization potential
- **Legacy Systems**: Often require specialized knowledge, affecting resource allocation

### Time Constraints
- **Urgent**: Focus on critical path optimization
- **Standard**: Use full decomposition benefits
- **Extended**: Add quality gates and validation steps

### Quality Requirements
- **Production Systems**: Add additional review and testing phases
- **Prototypes**: Streamline validation steps
- **Mission Critical**: Extensive parallel validation approaches
