# PromptWriter Sub-Agent Usage Guide

## Overview

The PromptWriter sub-agent is a specialized tool for creating high-quality, structured prompt files that guide complete development workflows. It ensures consistent, comprehensive prompts that can be executed by the WorkflowMaster sub-agent from issue creation through PR review.

## When to Use PromptWriter

Use the PromptWriter sub-agent when:

1. **Starting New Features**: Need a comprehensive prompt for feature development
2. **Complex Requirements**: Feature has multiple components and integration points
3. **Quality Standards**: Want to ensure prompt follows established patterns
4. **Workflow Integration**: Need complete workflow steps from issue to PR
5. **Knowledge Capture**: Want to document technical analysis and decisions

## How to Invoke PromptWriter

### Basic Invocation
```
/agent:prompt-writer

I need to implement [feature name] that will [brief description].
```

### Detailed Invocation with Context
```
/agent:prompt-writer

Context: I'm working on improving the graph query performance in Blarify
Requirements: Need to implement caching and query optimization
Constraints: Must maintain backward compatibility with existing API
Users: Developers analyzing large codebases (100k+ files)
```

## PromptWriter Process Flow

### 1. Requirements Gathering Phase

PromptWriter will ask comprehensive questions to understand:

- **Feature Scope**: What exactly needs to be implemented?
- **Problem Context**: What problems does this solve?
- **User Impact**: Who benefits and how?
- **Technical Constraints**: What limitations exist?
- **Success Metrics**: How will success be measured?

**Example Questions:**
- "What specific functionality should this feature provide?"
- "What problems with the current system does this address?"
- "Are there existing features this should integrate with?"
- "What are the performance or scalability requirements?"
- "How will users interact with this feature?"

### 2. Research and Analysis Phase

PromptWriter will:

- Analyze existing codebase for related patterns
- Identify integration points and dependencies
- Research current implementation approaches
- Document architectural considerations

**Research Activities:**
- Search for similar existing features
- Examine current API patterns
- Identify potential conflicts or dependencies
- Review test patterns and conventions

### 3. Prompt Creation Phase

PromptWriter creates a structured prompt with:

- **Clear Problem Statement**: Articulates the need and context
- **Comprehensive Requirements**: Functional and technical specifications
- **Technical Analysis**: Current state and proposed approach
- **Implementation Plan**: Phased development approach
- **Testing Strategy**: Unit, integration, and performance testing
- **Success Criteria**: Measurable outcomes
- **Complete Workflow**: Issue→Branch→Implementation→Testing→PR→Review

### 4. Quality Validation Phase

Before saving, PromptWriter validates:

- All required sections are present and complete
- Technical requirements are clear and implementable
- Implementation steps are actionable
- Success criteria are measurable
- Workflow includes all necessary steps

## Prompt Structure Template

PromptWriter creates prompts with this structure:

```markdown
# [Feature Name] Implementation

## Overview
[Brief description and context]

## Problem Statement
[Clear problem definition and motivation]

## Feature Requirements
### Functional Requirements
[What the feature must do]

### Technical Requirements
[Performance, security, compatibility constraints]

## Technical Analysis
### Current Implementation Review
[What exists today]

### Proposed Technical Approach
[How to implement the solution]

### Architecture Integration
[How it fits with existing systems]

## Implementation Plan
### Phase 1: [Foundation]
[Basic infrastructure and setup]

### Phase 2: [Core Features] 
[Main functionality implementation]

### Phase 3: [Advanced Features]
[Additional capabilities and optimization]

### Phase 4: [Testing and Documentation]
[Comprehensive testing and docs]

## Testing Requirements
### Unit Testing Strategy
[Individual component testing]

### Integration Testing
[Cross-component testing]

### Performance Testing
[Scalability and performance validation]

## Success Criteria
[Measurable outcomes and quality metrics]

## Implementation Steps
[Complete workflow from issue to PR]
```

## Best Practices for Working with PromptWriter

### Preparation Tips

1. **Gather Context**: Have clear understanding of the feature need
2. **Research Background**: Know related existing features
3. **Define Constraints**: Understand technical and business limitations
4. **Consider Users**: Think about who will use the feature and how

### During the Session

1. **Be Specific**: Provide detailed answers to PromptWriter questions
2. **Share Examples**: Reference similar features or implementations
3. **Discuss Tradeoffs**: Mention alternative approaches considered
4. **Define Success**: Be clear about what success looks like

### Quality Indicators

A good prompt from PromptWriter will have:

- **Clear Problem Statement**: Anyone can understand what's being solved
- **Actionable Requirements**: Specific enough to implement
- **Realistic Scope**: Achievable within reasonable timeframe
- **Comprehensive Testing**: Covers edge cases and integration
- **Measurable Success**: Clear criteria for completion

## Integration with WorkflowMaster

Prompts created by PromptWriter are designed for WorkflowMaster execution:

### Automatic Workflow Execution
```
/agent:workflow-master

Execute the complete workflow described in /prompts/[your-prompt-file].md
```

### Prompt Structure for WorkflowMaster

PromptWriter ensures prompts include:

- **Parseable Sections**: Clear headers and structure
- **Actionable Steps**: Specific implementation tasks
- **Complete Workflow**: All phases from issue to PR
- **Success Validation**: Criteria for each phase completion

## File Management

### Naming Conventions

PromptWriter saves files with descriptive names:
- `feature-graph-caching-system.md`
- `improve-query-performance.md`
- `add-multi-language-support.md`

### Location
All prompts saved to `/prompts/` directory for easy discovery and execution.

### Version Control
Prompts are committed to git for:
- Historical tracking of feature development
- Team collaboration and review
- Documentation of technical decisions

## Example Usage Sessions

### Example 1: New Feature Development
```
User: /agent:prompt-writer

I need to add real-time collaboration features to Blarify so multiple developers can work on the same codebase analysis simultaneously.

PromptWriter: I'll help you create a comprehensive prompt for real-time collaboration. Let me ask some questions to ensure we capture all requirements:

1. What specific collaboration features do you envision? (shared views, concurrent editing, chat, etc.)
2. How many concurrent users should be supported?
3. What are the technical constraints for real-time communication?
4. How should conflicts be resolved when users make simultaneous changes?
5. What's the expected user workflow for collaboration?

[... interactive session continues ...]

PromptWriter: Based on our discussion, I've created a comprehensive prompt at `/prompts/real-time-collaboration-features.md`. This prompt includes:
- Detailed analysis of real-time sync requirements
- WebSocket architecture for live updates
- Conflict resolution strategies
- Performance considerations for multiple users
- Complete implementation workflow

The prompt is ready for WorkflowMaster execution.
```

### Example 2: Performance Optimization
```
User: /agent:prompt-writer

Context: Graph queries are slow on large codebases
Requirements: Need caching and query optimization
Constraints: Must maintain API compatibility
Users: Developers with 100k+ file projects

PromptWriter: I understand you need graph query performance optimization. Let me gather more details:

1. What specific query patterns are slowest?
2. What performance targets are you aiming for?
3. Are there memory constraints to consider?
4. Should caching be in-memory, Redis, or both?
5. How will performance improvements be measured?

[... session continues with technical deep-dive ...]

PromptWriter: I've created a detailed prompt at `/prompts/graph-performance-optimization.md` with:
- Comprehensive performance analysis
- Multi-phase implementation plan
- Caching architecture design
- Benchmarking and testing strategy
- Complete development workflow

Ready for WorkflowMaster execution.
```

## Troubleshooting Common Issues

### Issue: Prompt Too Vague
**Problem**: Generated prompt lacks specific implementation details
**Solution**: Provide more specific requirements and examples during gathering phase
**Prevention**: Come prepared with clear feature requirements and constraints

### Issue: Missing Technical Context
**Problem**: Prompt doesn't integrate well with existing codebase
**Solution**: PromptWriter will research existing patterns, but provide known integration points
**Prevention**: Share relevant existing features and architectural decisions

### Issue: Unrealistic Scope
**Problem**: Prompt describes feature too large for single implementation
**Solution**: PromptWriter will suggest phased approach, confirm scope boundaries
**Prevention**: Discuss scope and timeline expectations upfront

### Issue: Workflow Steps Missing
**Problem**: Implementation steps don't include complete workflow
**Solution**: PromptWriter validates workflow completeness, but verify all steps present
**Prevention**: Review final prompt before accepting to ensure all phases included

## Tips for Success

### For Feature Requesters
1. **Define Clear Outcomes**: Know what success looks like
2. **Understand Users**: Articulate who benefits and how
3. **Consider Integration**: Think about existing system impact
4. **Provide Examples**: Reference similar features or competitors

### For Technical Implementation
1. **Review Existing Code**: Understand current patterns before prompting
2. **Consider Architecture**: Think about system-wide impacts
3. **Plan for Testing**: Consider what testing approaches make sense
4. **Document Decisions**: Capture why certain approaches were chosen

### For Project Management
1. **Scope Appropriately**: Balance ambition with deliverability
2. **Plan Phases**: Break large features into manageable chunks
3. **Define Metrics**: Ensure success can be measured objectively
4. **Consider Timeline**: Align scope with available resources

## Advanced Usage Patterns

### Creating Prompt Templates
Use PromptWriter to create reusable templates for common scenarios:
- Bug fix prompts
- Performance optimization prompts
- New feature development prompts
- Integration and migration prompts

### Multi-Phase Projects
For large features, create multiple related prompts:
- Phase 1 prompt for foundation
- Phase 2 prompt for core features
- Phase 3 prompt for advanced capabilities

### Cross-Team Collaboration
Use PromptWriter prompts as:
- Technical specification documents
- Implementation planning artifacts
- Progress tracking and review materials
- Knowledge transfer documentation

## Continuous Improvement

PromptWriter improves over time by:
- Learning from successful prompt patterns
- Incorporating feedback from WorkflowMaster execution
- Updating templates based on project evolution
- Adapting to new architectural patterns and technologies

Provide feedback on prompt quality and effectiveness to help improve future prompt generation.

## Support and Feedback

When working with PromptWriter:
- Be patient during the requirements gathering phase
- Provide detailed, specific information when asked
- Review generated prompts carefully before accepting
- Share feedback on prompt quality and execution success

The goal is to create prompts that result in successful, high-quality feature implementations with minimal back-and-forth clarification during execution.