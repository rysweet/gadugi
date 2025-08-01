# PromptWriter Sub-Agent Implementation Prompt

## Overview

We need to implement a specialized prompt-writing sub-agent for the Blarify project that can be invoked at the start of new working sessions to create high-quality, structured prompt files. This sub-agent will ensure consistent, comprehensive prompts that guide the coding agent through the complete development workflow from issue creation to PR review.

## Motivation

Creating well-structured prompts is crucial for successful AI-assisted development. However, prompt quality can vary significantly, leading to:
1. Incomplete feature specifications
2. Missing workflow steps (testing, documentation, PR creation)
3. Inconsistent formatting across different features
4. Lack of clear success criteria
5. Insufficient technical context

A specialized PromptWriter sub-agent can:
1. Ensure all prompts follow proven patterns and best practices
2. Include comprehensive workflow steps from planning to deployment
3. Provide clear technical specifications and success criteria
4. Maintain consistency across all feature development
5. Integrate seamlessly with the WorkflowMaster for execution

## Requirements

### Technical Requirements

1. **Claude Code Sub-Agent**: Must follow Claude Code sub-agent patterns with proper YAML frontmatter
2. **Tool Access**: Needs Read, Write, Grep, LS, WebSearch tools for research and file creation
3. **Template Knowledge**: Should understand and apply the observed prompt patterns
4. **Integration**: Must save prompts in `/prompts/` directory with descriptive filenames

### Functional Requirements

The sub-agent should:

1. **Gather Requirements**: Understand the feature request through conversation
2. **Research Context**: Analyze existing codebase and similar features
3. **Structure Content**: Create prompts following the established pattern:
   - Overview and context
   - Problem statement
   - Feature requirements
   - Technical analysis
   - Implementation plan
   - Testing requirements
   - Success criteria
   - Workflow steps
4. **Include Workflow**: Ensure each prompt includes complete workflow:
   - Issue creation
   - Branch creation
   - Research and planning
   - Implementation
   - Testing
   - PR creation
   - Code review invocation

### Prompt Structure Template

Every prompt should include these sections:

1. **Introduction**: Context about Blarify and the specific area of focus
2. **Problem Statement**: Clear description of what needs to be solved
3. **Feature Requirements**: Detailed functional and technical requirements
4. **Technical Analysis**: Current implementation review and proposed changes
5. **Implementation Plan**: Phased approach with clear milestones
6. **Testing Requirements**: Comprehensive test strategy
7. **Success Criteria**: Measurable outcomes
8. **Implementation Steps**: Detailed workflow from issue to PR

## Implementation Plan

### Phase 1: Create PromptWriter Sub-Agent

1. Create `.claude/agents/prompt-writer.md` with:
   - Proper YAML frontmatter for tools and description
   - Clear instructions on prompt structure
   - Template sections to include
   - Best practices for technical writing

2. Define prompt quality checklist:
   - Completeness of requirements
   - Technical accuracy
   - Workflow integration
   - Testing coverage
   - Success measurability

### Phase 2: Template Development

1. Create internal templates for common scenarios:
   - New feature development
   - Bug fixes and improvements
   - Test coverage enhancement
   - Documentation updates
   - Performance optimization

2. Include section templates with guiding questions:
   - What problem does this solve?
   - Who are the users/stakeholders?
   - What are the technical constraints?
   - How will we measure success?

### Phase 3: Workflow Integration

1. Ensure prompts always include:
   - GitHub issue creation with detailed description
   - Feature branch naming convention
   - Research phase with specific areas to investigate
   - Implementation phases with clear deliverables
   - Test-driven development approach
   - PR creation with comprehensive description and AI agent attribution
   - Code review agent invocation
   - Note: All GitHub interactions (issues, PRs, comments) must include AI agent attribution

2. Add metadata section for:
   - Estimated complexity
   - Required expertise areas
   - Dependencies on other features
   - Risk assessment

### Phase 4: Quality Assurance

1. Validation checks for:
   - All required sections present
   - Technical feasibility
   - Testability of requirements
   - Clear success metrics
   - Complete workflow steps

2. Integration with WorkflowMaster:
   - Prompts formatted for easy parsing
   - Clear action items identified
   - Dependencies explicitly stated

## Expected Outcomes

1. **Consistent Quality**: All feature prompts meet high standards
2. **Complete Workflows**: No missing steps from planning to deployment
3. **Clear Requirements**: Unambiguous technical specifications
4. **Efficient Development**: Reduced back-and-forth clarifications
5. **Knowledge Capture**: Best practices embedded in every prompt

## Success Criteria

- PromptWriter generates complete, actionable prompts
- All prompts include full workflow from issue to PR
- Technical specifications are clear and implementable
- Testing requirements are comprehensive
- WorkflowMaster can execute prompts without clarification
- 90%+ of prompts require no significant revisions

## Example Usage

When invoked at the start of a session:

1. PromptWriter asks about the feature/task to implement
2. Researches relevant codebase areas and documentation
3. Drafts comprehensive prompt following the template
4. Reviews prompt for completeness and accuracy
5. Saves to `/prompts/` with descriptive filename
6. Confirms readiness for WorkflowMaster execution

## Next Steps

1. Create GitHub issue for PromptWriter implementation
2. Create feature branch
3. Implement the sub-agent in `.claude/agents/prompt-writer.md`
4. Create example prompts demonstrating the pattern
5. Test with various feature types
6. Document usage guidelines
7. Create PR and invoke code reviewer