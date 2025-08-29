# Contributor Guide

## Dev Environment Tips

- Run `make` to create a virtual environment and install dependencies.
- Activate the virtual environment with `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows).

## Testing Instructions

- Run `make format` to format the code.
- Run `make lint` to check for linting errors.
- Run `make test` to run the tests.

## Implementation Philosophy

This section outlines the core implementation philosophy and guidelines for software development projects. It serves as a central reference for decision-making and development approach throughout the project.

### Core Philosophy

Embodies a Zen-like minimalism that values simplicity and clarity above all. This approach reflects:

- **Wabi-sabi philosophy**: Embracing simplicity and the essential. Each line serves a clear purpose without unnecessary embellishment.
- **Occam's Razor thinking**: The solution should be as simple as possible, but no simpler.
- **Trust in emergence**: Complex systems work best when built from simple, well-defined components that do one thing well.
- **Present-moment focus**: The code handles what's needed now rather than anticipating every possible future scenario.
- **Pragmatic trust**: The developer trusts external systems enough to interact with them directly, handling failures as they occur rather than assuming they'll happen.

This development philosophy values clear documentation, readable code, and belief that good architecture emerges from simplicity rather than being imposed through complexity.

### Core Design Principles

#### 1. Ruthless Simplicity

- **KISS principle taken to heart**: Keep everything as simple as possible, but no simpler
- **Minimize abstractions**: Every layer of abstraction must justify its existence
- **Start minimal, grow as needed**: Begin with the simplest implementation that meets current needs
- **Avoid future-proofing**: Don't build for hypothetical future requirements
- **Question everything**: Regularly challenge complexity in the codebase

#### 2. Architectural Integrity with Minimal Implementation

- **Preserve key architectural patterns**: Example: MCP for service communication, SSE for events, separate I/O channels, etc.
- **Implement patterns simply**: Use the simplest code that correctly implements the pattern
- **Maintain conceptual clarity**: The architecture should be understandable at a glance
- **Ensure proper separation**: Keep concerns properly separated even with minimal code

#### 3. Code Quality Through Simplicity

- **Readable over clever**: Code should be immediately understandable
- **Clear variable names**: Use descriptive names that eliminate need for comments
- **Small, focused functions**: Each function does one thing well
- **Minimal external dependencies**: Each dependency must strongly justify its inclusion
- **Direct error handling**: Handle errors where they occur, clearly and simply

#### 4. Documentation as Essential, Not Extra

- **Self-documenting code**: The code itself should tell the story
- **Strategic comments**: Comment on WHY, not WHAT
- **Minimal but complete docs**: Just enough documentation to understand and use the system
- **Examples over explanations**: Show how to use it rather than explaining at length

### Development Approach

#### Start Simple, Stay Simple

1. **Begin with the core**: Implement the essential functionality first
2. **Add only when needed**: New features only when there's a clear, present need
3. **Refactor ruthlessly**: Continuously simplify as the codebase grows
4. **Remove unused code**: If it's not being used, delete it
5. **Question additions**: Every new line of code should justify its existence

#### Incremental Development

1. **Small, working increments**: Each change should leave the system in a working state
2. **Test as you go**: Simple tests that verify the code works
3. **Iterate based on real needs**: Let actual usage drive development
4. **Avoid big rewrites**: Evolve the system gradually

#### Error Handling Philosophy

1. **Fail fast and clearly**: When something goes wrong, make it obvious
2. **Handle errors at the right level**: Deal with errors where you have context
3. **Simple recovery strategies**: Basic retry logic or graceful degradation
4. **Trust the system**: Don't over-engineer for unlikely failure scenarios
5. **Log what matters**: Capture enough information to diagnose issues

### Anti-Patterns to Avoid

#### Complexity Creep

- **Over-engineering**: Building complex solutions for simple problems
- **Premature optimization**: Optimizing before you know it's needed
- **Abstraction addiction**: Creating abstractions without clear benefit
- **Framework fixation**: Using heavy frameworks for simple tasks
- **Pattern overuse**: Applying design patterns where they don't add value

#### Development Pitfalls

- **Analysis paralysis**: Overthinking instead of implementing
- **Perfect is the enemy**: Seeking perfection instead of good enough
- **Scope creep**: Adding features that weren't requested
- **Technology chasing**: Using new tech for its own sake
- **Documentation debt**: Writing extensive docs for simple code

### Testing Philosophy

#### Simple, Effective Testing

1. **Test what matters**: Focus on critical paths and edge cases
2. **Simple test cases**: Each test should verify one thing
3. **Fast feedback**: Tests should run quickly
4. **Minimal mocking**: Mock only when absolutely necessary
5. **Real-world scenarios**: Test with realistic data and conditions

#### Test-Driven Simplicity

1. **Write tests first**: But keep them simple
2. **Red-green-refactor**: But focus on the refactor step
3. **Coverage as a guide**: Not a goal in itself
4. **Integration over unit**: Prefer testing actual behavior over isolated units

### Code Review Guidelines

#### What to Look For

1. **Unnecessary complexity**: Can this be simpler?
2. **Clear purpose**: Is it obvious what this code does?
3. **Proper scope**: Does this change do too much?
4. **Justified additions**: Does each new line earn its place?
5. **Maintainability**: Will this be easy to understand in 6 months?

#### Review Philosophy

- **Simplicity first**: Prioritize simplicity in feedback
- **Question complexity**: Challenge any unnecessary complexity
- **Suggest alternatives**: Offer simpler approaches
- **Praise clarity**: Recognize particularly clear, simple solutions
- **Learn from simplicity**: Share examples of elegant simplicity

### Maintenance and Evolution

#### Keeping It Simple Over Time

1. **Regular refactoring**: Continuously simplify the codebase
2. **Debt prevention**: Address complexity as it appears
3. **Deprecation courage**: Remove features that aren't providing value
4. **Consolidation**: Merge similar functionality
5. **Documentation pruning**: Keep docs current and minimal

#### Scaling Simplicity

1. **Modular simplicity**: Keep modules simple and independent
2. **Service boundaries**: Clear, simple interfaces between services
3. **Data simplicity**: Simple data structures and schemas
4. **Process simplicity**: Simple deployment and operational processes

### Decision Framework

When making technical decisions, ask:

1. **Is this the simplest solution that works?**
2. **What can we remove while keeping functionality?**
3. **Will this be obvious to someone reading it later?**
4. **Are we solving a real, current problem?**
5. **Can we defer this decision until we know more?**

### Examples of Simplicity in Practice

#### Good: Simple and Clear

```python
def calculate_discount(price, discount_percent):
    """Apply a percentage discount to a price."""
    return price * (1 - discount_percent / 100)
```

#### Bad: Over-Engineered

```python
class DiscountCalculator:
    def __init__(self, strategy_factory):
        self.strategy = strategy_factory.create_strategy()

    def calculate(self, price, discount):
        return self.strategy.apply(price, discount)
```

### Final Thoughts

Remember: The goal is not to write less code at any cost, but to write the **right amount** of code - no more, no less. Every line should have a clear purpose, every abstraction should pay for itself, and the overall system should be as simple as possible while still solving the problem at hand.

This philosophy is not about being lazy or cutting corners. It's about respecting the complexity of software development by not adding to it unnecessarily. It's about creating systems that are a joy to work with, easy to understand, and simple to maintain.

**In essence: Build what's needed, when it's needed, as simply as possible.**
