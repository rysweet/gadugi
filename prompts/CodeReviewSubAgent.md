# Code Review Sub-Agent Implementation Prompt

## Overview

We need to implement a specialized code review sub-agent for the Gadugi project that can be invoked to perform thorough, consistent code reviews on pull requests. This sub-agent will enhance our development workflow by providing automated, high-quality code reviews following best practices.

## Motivation

As the Gadugi codebase grows, maintaining consistent code quality across all contributions becomes challenging. Manual code reviews can vary in thoroughness and may miss important issues. A specialized sub-agent can:

1. Ensure consistent review standards across all PRs
2. Catch security vulnerabilities and performance issues
3. Verify adequate test coverage
4. Maintain code style and architectural patterns
5. Document learnings for continuous improvement

## Requirements

### Technical Requirements

1. **Claude Code Sub-Agent**: Must follow Claude Code sub-agent patterns with proper YAML frontmatter
2. **Tool Access**: Needs read, grep, ls, bash, web_search, web_fetch, and todo_write tools
3. **Integration**: Must work with existing GitHub PR workflow using `gh` CLI
4. **Memory**: Should maintain project-specific learnings in `.github/CodeReviewerProjectMemory.md`

### Functional Requirements

The sub-agent should:

1. **Analyze PR Changes**: Fetch and understand all modifications in a PR
2. **Apply Review Checklist**: Systematically check for:
   - Code quality and style compliance
   - Security vulnerabilities
   - Performance implications
   - Test coverage adequacy
   - Documentation completeness
3. **Provide Structured Feedback**: Generate clear, actionable review comments
4. **Learn and Improve**: Document patterns and insights for future reviews

### Review Categories

#### Code Quality
- Style guide compliance (Black, flake8)
- Clear naming conventions
- DRY and SOLID principles
- Proper error handling
- No debug code or TODOs

#### Security
- Input validation
- No hardcoded secrets
- Safe database queries
- Secure file operations
- Dependency vulnerabilities

#### Performance
- Efficient algorithms and data structures
- Optimized database queries
- Proper async/generator usage
- Resource management
- Caching strategies

#### Testing
- Unit test coverage
- Edge case handling
- Test isolation
- Mock usage
- Clear test descriptions

#### Documentation
- Function docstrings
- Complex logic comments
- README updates
- API documentation
- Migration guides

## Implementation Plan

### Phase 1: Create Sub-Agent Structure

1. Create `.claude/agents/code-reviewer.md` with:
   - Proper YAML frontmatter
   - Clear role definition
   - Review process steps
   - Output format specification

2. Define review checklist covering:
   - General code quality
   - Language-specific checks
   - Security considerations
   - Performance analysis
   - Testing requirements

### Phase 2: Project Integration

1. Create `.github/CodeReviewerProjectMemory.md` for storing:
   - Review insights
   - Common patterns
   - Project conventions
   - Technical decisions

2. Configure GitHub integration:
   - PR fetching commands
   - Diff analysis
   - Comment posting

### Phase 3: Gadugi-Specific Focus

Add specialized checks for:
- Graph operations and node management
- Tree-sitter parsing edge cases
- LSP server lifecycle
- Database transaction handling
- LLM integration patterns

### Phase 4: Testing and Refinement

1. Test on sample PRs
2. Refine review criteria based on feedback
3. Update memory with learnings
4. Document best practices

## Expected Outcomes

1. **Consistent Reviews**: All PRs receive thorough, standardized reviews
2. **Faster Feedback**: Automated initial review reduces wait times
3. **Knowledge Capture**: Project patterns documented automatically
4. **Quality Improvement**: Fewer bugs reach production
5. **Developer Growth**: Clear feedback helps team improve

## Success Criteria

- Sub-agent successfully reviews PRs with actionable feedback
- Review quality matches or exceeds manual reviews
- False positive rate < 10%
- Developer satisfaction with review helpfulness
- Measurable reduction in post-merge issues

## Next Steps

1. Create GitHub issue documenting this implementation plan
2. Create feature branch for the work
3. Implement sub-agent following Claude Code documentation
4. Test on recent PRs to validate effectiveness
5. Iterate based on team feedback
