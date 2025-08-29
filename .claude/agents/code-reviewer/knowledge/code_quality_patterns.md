# Code Quality Patterns and Issues

This document outlines common code quality issues and how to identify them during reviews.

## Structural Issues

### Complex Functions
**Pattern**: Functions with high cyclomatic complexity (>10 branches)
**Indicators**:
- Multiple nested if/else statements
- Long parameter lists (>5 parameters)
- Functions exceeding 50 lines
- Multiple early returns without clear logic

**Detection**:
```python
# Bad: High complexity
def process_user_data(user, action, permissions, context, options):
    if user is None:
        return None
    if action == "create":
        if permissions["can_create"]:
            if context == "admin":
                if options.get("force"):
                    # ... complex logic
                else:
                    # ... different logic
            else:
                # ... more logic
        else:
            return False
    # ... continues
```

**Recommendation**: Break into smaller, focused functions

### Code Duplication
**Pattern**: Repeated code blocks with minor variations
**Indicators**:
- Similar function structures across files
- Copy-pasted error handling
- Repeated validation logic

**Detection**: Look for similar patterns within 20% code similarity

### Poor Naming
**Pattern**: Unclear or misleading identifiers
**Indicators**:
- Single letter variables (except loops)
- Abbreviations without context (`usr`, `calc`, `mgr`)
- Misleading names (`data` for user objects)
- Hungarian notation in Python

## Design Issues

### Tight Coupling
**Pattern**: Classes/modules with excessive dependencies
**Indicators**:
- Import statements >15 per file
- Circular dependencies
- Direct database access in presentation layer
- Hardcoded external service URLs

### Violation of Single Responsibility
**Pattern**: Classes doing multiple unrelated tasks
**Indicators**:
- Class names with "and" or "Manager"
- Methods with unrelated functionality
- Mixed business logic and presentation

**Example**:
```python
# Bad: Multiple responsibilities
class UserAccountManager:
    def create_user(self):
        pass
    def send_email(self):  # Should be separate
        pass
    def generate_report(self):  # Should be separate
        pass
```

### Inappropriate Use of Inheritance
**Pattern**: Inheritance used for code reuse rather than "is-a" relationships
**Indicators**:
- Deep inheritance hierarchies (>3 levels)
- Overriding most parent methods
- Composition would be more appropriate

## Error Handling Issues

### Bare Exception Handling
**Pattern**: Catching all exceptions without specificity
```python
# Bad
try:
    risky_operation()
except:  # Too broad
    pass  # Silent failure
```

### Resource Leaks
**Pattern**: Not properly closing resources
**Indicators**:
- File operations without context managers
- Database connections not closed
- Network sockets left open

**Good Pattern**:
```python
# Good: Use context managers
with open("file.txt") as f:
    content = f.read()
```

## Performance Issues

### Inefficient Data Structures
**Pattern**: Wrong data structure for the use case
**Indicators**:
- Using lists for frequent membership tests
- Not using sets for unique collections
- Unnecessary nested loops

**Example**:
```python
# Bad: O(n) lookup
if item in my_list:  # Use set instead

# Good: O(1) lookup
if item in my_set:
```

### Premature String Concatenation
**Pattern**: Building strings inefficiently
```python
# Bad: Creates new string objects
result = ""
for item in items:
    result += str(item)

# Good: More efficient
result = "".join(str(item) for item in items)
```

### N+1 Query Problems
**Pattern**: Database queries in loops
**Detection**: ORM queries inside iteration
**Solution**: Use bulk operations or eager loading

## Maintainability Issues

### Magic Numbers and Strings
**Pattern**: Hardcoded values without explanation
```python
# Bad
if user.age > 18:  # Why 18?
    return "APPROVED"  # Magic string

# Good
LEGAL_AGE = 18
APPROVAL_STATUS = "APPROVED"
if user.age > LEGAL_AGE:
    return APPROVAL_STATUS
```

### Inconsistent Formatting
**Pattern**: Mixed code styles within project
**Indicators**:
- Mixed indentation (tabs/spaces)
- Inconsistent naming conventions
- Variable line lengths

### Missing Documentation
**Pattern**: Code without adequate documentation
**Indicators**:
- Public methods without docstrings
- Complex algorithms without comments
- Missing type hints in Python

## Testing Issues

### Poor Test Coverage
**Pattern**: Insufficient or ineffective tests
**Indicators**:
- Coverage below 80%
- Missing edge case tests
- No negative test cases

### Test Code Duplication
**Pattern**: Repeated setup code in tests
**Solution**: Use fixtures and test utilities

### Brittle Tests
**Pattern**: Tests that fail due to unrelated changes
**Indicators**:
- Tests dependent on external services
- Hardcoded dates/times
- Order-dependent tests

## Anti-Patterns to Flag

### God Object
- Classes with >20 methods
- Classes with >500 lines
- Classes handling multiple domains

### Spaghetti Code
- Functions with >5 levels of nesting
- Goto-style logic flow
- Unclear control flow

### Copy-Paste Programming
- Identical code blocks
- Similar function signatures
- Repeated error messages

## Quality Metrics to Track

### Complexity Metrics
- Cyclomatic complexity per function
- Cognitive complexity
- Depth of inheritance

### Size Metrics
- Lines of code per file/class/method
- Number of parameters
- Number of local variables

### Coupling Metrics
- Afferent/efferent coupling
- Dependency cycles
- Interface segregation

## Automated Detection

### Tools Integration
- **Ruff**: Style and basic quality issues
- **Mypy**: Type checking and related quality issues
- **Bandit**: Security-related quality issues
- **Radon**: Complexity metrics

### Custom Rules
- Project-specific naming conventions
- Architecture compliance
- Business rule validation

## Review Prioritization

### High Priority (Must Fix)
- Security vulnerabilities
- Resource leaks
- Data corruption risks
- Critical performance issues

### Medium Priority (Should Fix)
- High complexity functions
- Code duplication
- Poor error handling
- Missing tests

### Low Priority (Nice to Fix)
- Style inconsistencies
- Minor naming issues
- Documentation gaps
- Non-critical performance optimizations

## Contextual Considerations

### Team Experience Level
- Junior teams: Focus on fundamentals
- Senior teams: Advanced design patterns
- Mixed teams: Clear, simple patterns

### Project Phase
- Early development: Flexibility over perfection
- Maintenance: Stability and clarity
- Legacy systems: Gradual improvement

### Business Criticality
- High-stakes systems: Extra rigor
- Prototypes: Speed over perfection
- Public APIs: Interface stability
