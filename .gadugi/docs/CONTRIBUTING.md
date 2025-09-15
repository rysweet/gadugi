# Contributing to Gadugi

> **Welcome to the Gadugi community!**
>
> Gadugi (gah-DOO-gee) embodies the Cherokee principle of communal work - where community members come together to accomplish tasks that benefit everyone through collective wisdom and mutual support.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Agent Development](#agent-development)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Community and Support](#community-and-support)

## Code of Conduct

This project follows the Cherokee values of Gadugi:
- **ᎠᏓᏅᏙ (Adanvdo) - Collective Wisdom**: Share knowledge respectfully and learn from others
- **ᎠᎵᏍᏕᎸᏗ (Alisgelvdi) - Mutual Support**: Help fellow contributors and maintainers
- **ᎤᏂᎦᏚ (Unigadv) - Shared Resources**: Contribute to the common good

We are committed to providing a welcoming and inspiring community for all. Please be respectful, constructive, and helpful in all interactions.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.11+**: Required for running the system
- **UV Package Manager**: Fast Python dependency management
- **Git**: Version control with worktree support
- **GitHub CLI (`gh`)**: For PR and issue management
- **Docker** (optional): For containerized execution
- **VS Code** (recommended): With the Gadugi extension for enhanced workflow

### Quick Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/your-username/gadugi.git
cd gadugi

# 2. Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Set up development environment
uv sync --extra dev

# 4. Install pre-commit hooks
uv run pre-commit install

# 5. Verify setup
uv run pytest tests/ -v
uv run ruff check .
```

## Development Setup

### UV Development Environment

Gadugi uses [UV](https://github.com/astral-sh/uv) for dependency management:

```bash
# Install dependencies (creates .venv automatically)
uv sync --extra dev

# Run commands in the virtual environment
uv run python script.py
uv run pytest tests/
uv run ruff format .

# Add dependencies
uv add requests              # Runtime dependency
uv add --group dev pytest   # Development dependency
```

### Pre-commit Configuration

We use pre-commit hooks to maintain code quality:

```bash
# Install hooks (run once)
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files

# Update hook versions
uv run pre-commit autoupdate
```

### VS Code Extension

Install the Gadugi VS Code extension for enhanced development:

1. Install from VS Code Marketplace
2. Use `Ctrl+Shift+P` → "Gadugi: Bloom" to start Claude in all worktrees
3. Monitor development progress in the Gadugi sidebar panel

## Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

#### 🛠️ Code Contributions
- **New Agents**: Create specialized agents for specific tasks
- **Bug Fixes**: Fix issues in existing agents or core functionality
- **Feature Enhancements**: Improve existing capabilities
- **Performance Improvements**: Optimize execution speed or resource usage

#### 📚 Documentation
- **Guides and Tutorials**: Help new users understand the system
- **API Documentation**: Document agent interfaces and methods
- **Code Comments**: Improve code readability
- **Examples**: Provide real-world usage examples

#### 🧪 Testing
- **Test Coverage**: Add tests for untested code
- **Integration Tests**: Test agent interactions
- **Performance Tests**: Validate system performance
- **Edge Case Testing**: Test unusual or boundary conditions

#### 🐛 Issue Reports
- **Bug Reports**: Report issues with clear reproduction steps
- **Feature Requests**: Suggest new capabilities or improvements
- **Documentation Issues**: Point out unclear or missing documentation

### Contribution Workflow

**IMPORTANT**: Use the Gadugi orchestrator agents rather than manual processes:

#### For Single Features or Fixes
```bash
# Use WorkflowManager for complete development workflow
/agent:WorkflowManager

Task: Implement [description of feature/fix]
Requirements:
- [Specific requirements]
- [Testing requirements]
- [Documentation updates]
```

#### For Multiple Related Tasks
```bash
# Use OrchestratorAgent for parallel execution
/agent:OrchestratorAgent

Execute these tasks in parallel:
- [Task 1 description]
- [Task 2 description]
- [Task 3 description]
```

#### Manual Process (Discouraged)
Only use manual processes for:
- Simple documentation fixes
- Single-line code changes
- Emergency hotfixes

### Git Workflow

1. **Create Feature Branch**: Use descriptive naming
   ```bash
   git checkout -b feature/issue-123-agent-enhancement
   ```

2. **Make Focused Commits**: Small, logical commits with clear messages
   ```bash
   git commit -m "feat: add retry logic to GitHub operations

   - Implement exponential backoff for API calls
   - Add circuit breaker pattern
   - Include comprehensive test coverage

   Fixes #123"
   ```

3. **Use Conventional Commits**: Follow the [Conventional Commits](https://conventionalcommits.org/) specification
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `test:` - Testing improvements
   - `refactor:` - Code restructuring
   - `chore:` - Maintenance tasks

4. **Keep Branches Current**: Regularly rebase on main
   ```bash
   git fetch origin
   git rebase origin/main
   ```

## Agent Development

### Creating New Agents

Agents are the core building blocks of Gadugi. Follow these guidelines:

#### 1. Agent Structure

All agents follow a consistent structure in `.claude/agents/agent-name.md`:

```markdown
---
name: agent-name
version: 1.0.0
description: Brief description of agent purpose
tools:
  - Edit
  - Read
  - Bash
  - Grep
complexity: medium
maintainer: your-github-username
---

# Agent Name

## Purpose
[Clear description of what the agent does]

## Usage
```
/agent:agent-name

Context: [Describe the context]
Requirements: [List specific requirements]
```

## Implementation
[Detailed implementation instructions]
```

#### 2. Agent Categories

- **🔵 Orchestration**: Coordinate multiple agents or workflows
- **🟢 Implementation**: Perform core development tasks
- **🟣 Review**: Quality assurance and validation
- **🟠 Maintenance**: System health and administrative tasks

#### 3. Implementation Patterns

**Python Backend + Claude Agent** (for complex logic):
- Create Python module in `src/agents/`
- Implement shared interface from `interfaces.py`
- Create corresponding `.claude/agents/` markdown file
- Add tests in `tests/agents/`

**Pure Claude Agent** (for simple workflows):
- Create only the `.claude/agents/` markdown file
- Use Claude Code tools directly
- Focus on clear instructions and examples

### Agent Best Practices

#### Error Handling
```python
from error_handling import CircuitBreakerError, retry_with_backoff

@retry_with_backoff(max_attempts=3)
def risky_operation():
    # Implementation with automatic retries
    pass
```

#### State Management
```python
from state_management import WorkflowState

state = WorkflowState(task_id="task-123")
state.update_phase("implementation")
state.save_checkpoint()
```

#### GitHub Operations
```python
from github_operations import GitHubClient

client = GitHubClient()
client.create_issue(title="Feature Request", body="Description")
```

## Testing Requirements

### Test Coverage Standards

- **Minimum 80% coverage** for new code
- **100% coverage** for critical paths (authentication, data integrity)
- **Integration tests** for agent interactions
- **Performance tests** for optimization-focused changes

### Testing Strategy

#### Unit Tests
```bash
# Run specific test file
uv run pytest tests/agents/test_new_agent.py -v

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=html

# Run tests matching pattern
uv run pytest -k "test_github_operations"
```

#### Integration Tests
```bash
# Run integration test suite
uv run pytest tests/integration/ -v

# Test specific agent integration
uv run pytest tests/integration/test_orchestrator_agent.py
```

#### Test Structure
```python
import pytest
from unittest.mock import Mock, patch
from agents.your_agent import YourAgent

class TestYourAgent:
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = YourAgent()

    def test_primary_functionality(self):
        """Test the main agent functionality."""
        result = self.agent.execute_task("test input")
        assert result.success
        assert "expected output" in result.output

    @patch('agents.your_agent.github_client')
    def test_github_integration(self, mock_client):
        """Test GitHub API interactions."""
        mock_client.create_issue.return_value = {"number": 123}
        result = self.agent.create_issue("Title", "Body")
        assert result["number"] == 123
```

### Quality Gates

All contributions must pass:

1. **Unit Tests**: `uv run pytest tests/ -v`
2. **Linting**: `uv run ruff check .`
3. **Formatting**: `uv run ruff format .`
4. **Type Checking**: `uv run mypy . --ignore-missing-imports`
5. **Pre-commit Hooks**: `uv run pre-commit run --all-files`

## Documentation Standards

### Documentation Types

#### Agent Documentation
- **Purpose**: Clear description of agent functionality
- **Usage Examples**: Real-world usage patterns
- **Implementation Notes**: Technical details
- **Error Handling**: Common issues and solutions

#### API Documentation
- **Function Signatures**: Complete parameter documentation
- **Return Values**: Type and structure documentation
- **Examples**: Working code samples
- **Error Cases**: Exception handling

#### Architecture Documentation
- **System Overview**: High-level architecture
- **Component Interactions**: How pieces fit together
- **Design Decisions**: Rationale for architectural choices
- **Future Considerations**: Scalability and evolution

### Documentation Style

- **Clear and Concise**: Avoid unnecessary jargon
- **Examples-Driven**: Show real usage patterns
- **Consistent Structure**: Follow established templates
- **Up-to-Date**: Update with code changes

### Markdown Standards

```markdown
# Main Title (H1 - only one per document)

## Section Title (H2)

### Subsection Title (H3)

#### Implementation Details (H4)

- Use bullet points for lists
- **Bold** for emphasis
- `code` for inline code
- ```language for code blocks

> **Note**: Use callouts for important information

> **Warning**: Use warnings for critical considerations
```

## Pull Request Process

### Pre-submission Checklist

Before submitting a pull request:

- [ ] **Code Quality**: All tests pass and linting is clean
- [ ] **Documentation**: Added/updated relevant documentation
- [ ] **Testing**: Added tests for new functionality
- [ ] **Commit Messages**: Follow conventional commit format
- [ ] **Branch**: Created from latest main branch
- [ ] **Scope**: PR focuses on a single feature or fix

### PR Title and Description

#### Title Format
```
type(scope): brief description

Examples:
feat(agents): add retry logic to workflow manager
fix(github): resolve API rate limit handling
docs(readme): update quick start instructions
```

#### Description Template
```markdown
## Summary
[Brief description of changes]

## Changes Made
- [Specific change 1]
- [Specific change 2]
- [Specific change 3]

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] Code comments added
- [ ] README updated (if needed)
- [ ] Agent documentation updated

## Breaking Changes
[List any breaking changes, or "None"]

## Related Issues
Fixes #123
Related to #456
```

### Review Process

1. **Automated Checks**: PR must pass all CI/CD checks
2. **Code Review**: At least one maintainer review required
3. **Documentation Review**: Ensure docs are clear and complete
4. **Testing Verification**: Verify test coverage and quality
5. **Merge**: Squash and merge after approval

### Addressing Review Feedback

When receiving review feedback:

1. **Acknowledge**: Respond to each comment
2. **Clarify**: Ask questions if feedback is unclear
3. **Implement**: Make requested changes
4. **Update**: Push changes and request re-review
5. **Resolve**: Mark conversations as resolved after addressing

## Community and Support

### Getting Help

- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Check existing guides and references
- **Code Examples**: Review existing agents for patterns

### Communication Guidelines

#### Issue Reporting
```markdown
## Bug Report

**Description**: Clear description of the issue

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Environment**:
- OS: [e.g., macOS 14.0]
- Python: [e.g., 3.11.5]
- Gadugi: [e.g., 1.2.3]

**Additional Context**: Any other relevant information
```

#### Feature Requests
```markdown
## Feature Request

**Problem**: What problem does this solve?

**Proposed Solution**: Detailed description of proposed feature

**Alternatives Considered**: Other approaches considered

**Additional Context**: Use cases, examples, references
```

### Recognition

Contributors are recognized through:

- **Contributor Credits**: Listed in README and documentation
- **GitHub Achievements**: Badges and contribution graphs
- **Community Highlights**: Featured contributions in releases
- **Maintainer Opportunities**: Path to becoming a maintainer

### Becoming a Maintainer

Regular contributors can become maintainers by:

1. **Consistent Contributions**: Regular, high-quality contributions
2. **Community Involvement**: Helping other contributors
3. **Technical Expertise**: Deep understanding of system architecture
4. **Communication Skills**: Clear, helpful communication
5. **Reliability**: Consistent availability and response times

## Advanced Contributing

### Performance Optimization

When contributing performance improvements:

- **Benchmark First**: Establish baseline performance
- **Profile Code**: Identify actual bottlenecks
- **Measure Impact**: Quantify improvements
- **Document Changes**: Explain optimization techniques

### Security Considerations

- **Validate Inputs**: Always sanitize user inputs
- **Secure Secrets**: Never commit credentials or tokens
- **Container Security**: Follow container security best practices
- **Audit Trails**: Maintain comprehensive logs

### Backward Compatibility

- **Deprecation Warnings**: Add warnings before removing features
- **Migration Guides**: Provide clear upgrade paths
- **Version Support**: Support previous major versions
- **API Stability**: Maintain stable public interfaces

---

## Thank You

Thank you for contributing to Gadugi! Your participation embodies the Cherokee spirit of communal work, helping create tools that benefit the entire development community.

*ᎤᎵᎮᎵᏍᏗ (Ulihelisdi) - "We are helping each other"*

---

**Questions?** Feel free to open an issue or start a discussion. The Gadugi community is here to help!
