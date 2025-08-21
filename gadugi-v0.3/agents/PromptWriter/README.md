# Prompt Writer Agent

The Prompt Writer Agent is a specialized component of the Gadugi v0.3 multi-agent system designed to create high-quality, structured prompt files for development workflows.

## Purpose

Creating well-structured prompts is crucial for successful AI-assisted development. The Prompt Writer Agent ensures:

- **Consistent Quality**: All prompts follow proven patterns and best practices
- **Complete Workflows**: From issue creation to PR merge
- **Clear Requirements**: Detailed specifications and success criteria
- **Context Integration**: Understanding of existing codebase patterns

## Key Features

### 🔍 **Intelligent Analysis**
- Extracts and refines feature requirements
- Analyzes existing codebase for integration points
- Research external dependencies and patterns

### 📝 **Structured Generation**
- Creates prompts following proven template structure
- Includes comprehensive workflow steps
- Defines clear, measurable success criteria

### 🔧 **Developer-Focused**
- Saves prompts with descriptive filenames
- Integrates seamlessly with orchestrator system
- Provides complete implementation guidance

## Usage

The Prompt Writer Agent can be invoked directly by the orchestrator or used interactively:

### Via Orchestrator
```python
# The orchestrator can use prompt-writer to create structured tasks
from orchestrator.run_agent import run_agent

result = run_agent("prompt-writer", "Add user authentication to web app")
```

### Interactive Usage
```bash
# Run directly for interactive prompt creation  
python src/orchestrator/run_agent.py prompt-writer "Add user authentication"
```

## Prompt Structure

Every generated prompt follows this comprehensive structure:

1. **Overview** - Brief description and context
2. **Problem Statement** - Clear problem definition
3. **Requirements** - Functional and technical needs
4. **Implementation Plan** - Phased development approach
5. **Success Criteria** - Measurable completion goals
6. **Workflow Steps** - Complete development process

## Integration

The Prompt Writer Agent integrates with other Gadugi v0.3 components:

- **Orchestrator**: Receives tasks and generates structured prompts
- **Task Decomposer**: Works with decomposed tasks to create detailed subtask prompts
- **Agent Runner**: Executes within the standard agent execution framework

## Quality Assurance

Every generated prompt is validated to include:
- ✅ Clear, actionable requirements
- ✅ Complete workflow from issue to merge
- ✅ Specific testing requirements
- ✅ Documentation needs
- ✅ Integration considerations
- ✅ Measurable success criteria

## Output

Prompts are saved as markdown files in the `/prompts/` directory with descriptive names:
- `implement-[feature-name].md`
- `fix-[issue-description].md`
- `enhance-[component-name].md`

## Example Output

A typical generated prompt includes:

```markdown
# User Authentication Implementation

## Overview
Implement secure user authentication system with email/password login...

## Requirements
### Functional Requirements
- User registration with email verification
- Secure password hashing and storage
- Login/logout functionality
- Session management

### Technical Requirements
- bcrypt for password hashing
- JWT tokens for session management
- Rate limiting for login attempts
- Integration with existing user models

## Implementation Plan
### Phase 1: Research and Setup
- Analyze existing user models
- Research security best practices
- Plan database schema updates

[... complete structured implementation guide]
```

## Contributing

The Prompt Writer Agent follows the Gadugi v0.3 agent standards:
- Structured markdown agent definition
- Integration with orchestrator framework
- Comprehensive documentation
- Test coverage for functionality

## Next Steps

Future enhancements may include:
- Template customization based on project type
- Integration with external documentation sources
- Automated code analysis for more accurate context
- Support for multiple output formats