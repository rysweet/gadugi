# System Design Review Agent Integration Guide

## Overview

The System Design Review Agent provides automated architectural review capabilities for the Gadugi project. This guide covers setup, configuration, usage, and integration with existing workflows.

## Architecture

The System Design Review Agent consists of several key components:

### Core Components

- **SystemDesignReviewer**: Main orchestrator class
- **ASTParserFactory**: Pluggable parser system for multiple languages
- **DocumentationManager**: Automated ARCHITECTURE.md maintenance
- **ADRGenerator**: Architecture Decision Record creation
- **GitHub Actions Integration**: Automated PR review workflow

### Integration Points

- **Enhanced Separation Architecture**: Uses shared modules for error handling, state management, and GitHub operations
- **Container Runtime**: Executes in secure, isolated containers
- **GitHub API**: Automated PR review and comment posting
- **Existing Agent Ecosystem**: Coordinates with WorkflowManager, OrchestratorAgent, and CodeReviewer

## Installation and Setup

### Prerequisites

- Python 3.9+
- GitHub CLI (`gh`) configured with appropriate permissions
- Access to repository with write permissions for PR reviews

### Dependencies

The agent requires the following Python packages:

```bash
# Core dependencies
pip install pathlib typing-extensions dataclasses-json

# For Enhanced Separation integration (if available)
pip install -e .  # Install Gadugi project dependencies
```

### Directory Structure

Ensure the following directories exist:

```
.claude/agents/system_design_reviewer/    # Agent implementation
tests/agents/system_design_reviewer/      # Test suite
docs/adr/                                 # Architecture Decision Records
.github/workflows/                        # GitHub Actions workflows
```

## Configuration

### Basic Configuration

The agent can be configured through the initialization parameters:

```python
config = {
    'max_pr_size': 1000,          # Maximum files to analyze per PR
    'analysis_timeout': 300,      # Timeout in seconds (5 minutes)
    'enable_adr': True,           # Enable ADR generation
    'enable_doc_updates': True,   # Enable documentation updates
}

reviewer = SystemDesignReviewer(config)
```

### GitHub Actions Configuration

The workflow is automatically triggered on:
- Pull request opened
- Pull request synchronized (new commits)
- Pull request reopened

Configuration options in `.github/workflows/system-design-review.yml`:

```yaml
# Customize file patterns to trigger review
paths:
  - '**.py'
  - '**.ts'
  - '**.tsx'
  - '.claude/agents/**'
  - '.claude/shared/**'

# Customize size limits
- name: Validate PR size
  run: |
    CHANGED_FILES=$(git diff --name-only ${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }} | wc -l)
    if [ $CHANGED_FILES -gt 500 ]; then
      echo "skip_review=true" >> $GITHUB_OUTPUT
    fi
```

## Usage

### Manual Invocation

```bash
# Basic PR analysis
python -c "
from .claude.agents.system_design_reviewer import SystemDesignReviewer
reviewer = SystemDesignReviewer()
result = reviewer.review_pr('123')
print(f'Impact: {result.architectural_impact.value}')
"

# Force ADR generation
python -c "
from .claude.agents.system_design_reviewer import SystemDesignReviewer
reviewer = SystemDesignReviewer()
result = reviewer.review_pr('123', force_adr=True)
"
```

### Agent Invocation Pattern

```bash
# Using Claude Code agent system
/agent:system-design-reviewer analyze-pr 123

# With additional options
/agent:system-design-reviewer analyze-pr 123 --force-adr --update-architecture
```

### Programmatic Usage

```python
from .claude.agents.system_design_reviewer import SystemDesignReviewer

# Initialize reviewer
reviewer = SystemDesignReviewer({
    'max_pr_size': 500,
    'enable_adr': True
})

# Review a PR
result = reviewer.review_pr(
    pr_number='123',
    force_adr=False,
    update_architecture=True
)

# Check results
if result.status == ReviewStatus.COMPLETED:
    print(f"Review completed with {result.architectural_impact.value} impact")
    print(f"Changes detected: {len(result.changes_detected)}")
    print(f"ADRs generated: {len(result.adrs_generated)}")
    print(f"Documentation updates: {len(result.documentation_updates)}")
else:
    print(f"Review failed: {result.review_comments}")
```

## Features

### AST-Based Code Analysis

The agent analyzes code changes using Abstract Syntax Tree parsing:

#### Supported Languages
- **Python**: Full support with pattern detection
- **TypeScript**: Basic support (expandable)

#### Detected Elements
- Classes and interfaces
- Functions and methods (including async)
- Imports and dependencies
- Decorators and annotations
- Architectural patterns

#### Pattern Recognition
- Singleton pattern
- Factory pattern
- Observer pattern
- Abstract base classes
- Context managers
- Async patterns

### Change Detection

The agent identifies several types of architectural changes:

#### Change Types
- **Added**: New architectural elements
- **Modified**: Changes to existing elements
- **Removed**: Deleted elements
- **Renamed**: Element name changes

#### Impact Assessment
- **Low**: Minor changes with minimal architectural impact
- **Medium**: Moderate changes affecting component interfaces
- **High**: Significant changes requiring review
- **Critical**: Changes with major architectural implications

### Documentation Management

#### ARCHITECTURE.md Updates

The agent automatically maintains the architecture document:

```markdown
# Sections Updated Automatically

## Component Architecture
- New components added to PR
- Modified component descriptions

## Agent Ecosystem
- Agent hierarchy changes
- New agent integrations

## Security Architecture
- Security-related changes
- XPIA defense updates

## Performance Architecture
- Async function changes
- Performance optimizations

## Evolution History
- High and critical impact changes
- ADR references
- Architectural implications
```

#### Update Process

1. **Change Analysis**: Identify which sections need updates
2. **Content Generation**: Generate section-specific content
3. **Document Merging**: Merge new content with existing structure
4. **Evolution Tracking**: Add entries to evolution history

### ADR Generation

Architecture Decision Records are generated for:

#### Trigger Conditions
- High or critical impact changes
- New architectural patterns
- Security architecture changes
- Performance architecture changes
- Integration changes
- Framework changes

#### ADR Structure
```markdown
# ADR-{number}: {Title}

**Date**: {date}
**Status**: Proposed
**Context**: PR #{number}

## Decision
{What was decided}

## Rationale
{Why this decision was made}

## Consequences
**Positive:**
- {Benefits}

**Negative:**
- {Costs and risks}

## Alternatives Considered
- {Alternative approaches}

## Implementation Notes
- {Technical details}

## Related Changes
- {PR and issue references}
```

### GitHub Integration

#### Review Process

1. **Automated Trigger**: GitHub Actions workflow starts on PR events
2. **Change Analysis**: AST parsing and impact assessment
3. **Documentation Updates**: ARCHITECTURE.md and ADR generation
4. **Review Posting**: Structured review comment on PR
5. **Artifact Storage**: Generated files stored as workflow artifacts

#### Review Output Format

```markdown
## System Design Review Summary

**Architectural Impact**: High
**Design Review**: 🔄 Changes Requested

*Note: This review was conducted by an AI agent on behalf of the repository owner.*

### Architectural Analysis

#### Components Affected
- **NewService**: Added new service architecture pattern
- **ServiceManager**: Modified initialization process

#### Design Pattern Compliance
- ✅ **Enhanced Separation**: Properly uses shared modules
- ⚠️ **Performance**: Consider async implementation

#### Architecture Decision Records
- 📝 **ADR-003**: Service Architecture Pattern - Generated for this change

### Documentation Updates
- Updated Component Architecture section
- Added evolution history entry

### Recommendations

#### Required Actions
- [ ] Add unit tests for new service patterns
- [ ] Update service documentation

#### Suggestions
- Consider implementing async service interfaces
- Review service dependency injection patterns
```

## Integration with Existing Agents

### WorkflowManager Integration

The System Design Review Agent integrates with WorkflowManager in Phase 9:

```bash
# Phase 9: Automatic invocation during workflow execution
# WorkflowManager automatically invokes system design review
# after PR creation (Phase 8)

# .claude/scripts/enforce_phase_9.sh includes:
/agent:system-design-reviewer analyze-pr $PR_NUMBER
```

### OrchestratorAgent Coordination

For parallel execution scenarios:

```bash
# OrchestratorAgent can invoke design review in parallel
# with other agents for comprehensive PR analysis

/agent:orchestrator-agent

Execute these agents in parallel:
- /agent:code-reviewer
- /agent:system-design-reviewer
- /agent:test-writer
```

### CodeReviewer Collaboration

The agents provide complementary reviews:

- **CodeReviewer**: Code quality, security, performance at implementation level
- **SystemDesignReviewer**: Architectural coherence, design patterns, system evolution

## Testing

### Running Tests

```bash
# Run all system design reviewer tests
pytest tests/agents/system_design_reviewer/ -v

# Run specific test modules
pytest tests/agents/system_design_reviewer/test_ast_parser.py -v
pytest tests/agents/system_design_reviewer/test_core.py -v
pytest tests/agents/system_design_reviewer/test_documentation_manager.py -v
pytest tests/agents/system_design_reviewer/test_adr_generator.py -v

# Check test coverage
pytest tests/agents/system_design_reviewer/ --cov=.claude.agents.system_design_reviewer --cov-report=html
```

### Test Structure

```
tests/agents/system_design_reviewer/
├── __init__.py
├── test_ast_parser.py          # AST parsing and change detection
├── test_core.py                # Main reviewer functionality
├── test_documentation_manager.py  # Documentation updates
└── test_adr_generator.py       # ADR generation
```

### Coverage Targets

- **Overall Coverage**: >80%
- **Core Components**: >90%
- **Error Handling**: >85%
- **Integration Points**: >75%

## Troubleshooting

### Common Issues

#### Agent Import Errors

```bash
# Error: Cannot import shared modules
# Solution: Ensure Enhanced Separation modules are available
pip install -e .  # Install project in development mode

# Or verify fallback implementations work
python -c "from .claude.agents.system_design_reviewer.fallbacks import GitHubOperations"
```

#### GitHub API Issues

```bash
# Error: GitHub CLI not authenticated
gh auth status
gh auth login

# Error: Insufficient permissions
# Ensure GitHub token has repo:write permissions
gh auth refresh -s write:discussion,repo
```

#### Large PR Handling

```bash
# Error: PR too large for analysis
# Solution: Adjust size limits in workflow or config

# In .github/workflows/system-design-review.yml:
if [ $CHANGED_FILES -gt 1000 ]; then  # Increase from 500
```

#### File Permission Issues

```bash
# Error: Cannot write ARCHITECTURE.md or ADRs
# Solution: Check directory permissions

mkdir -p docs/adr
chmod 755 docs/adr
touch ARCHITECTURE.md
chmod 644 ARCHITECTURE.md
```

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

reviewer = SystemDesignReviewer()
result = reviewer.review_pr('123')
```

#### Manual Testing

```python
# Test AST parsing
from .claude.agents.system_design_reviewer.ast_parser import PythonASTParser
parser = PythonASTParser()
elements = parser.parse_file('path/to/file.py')
print(f"Found {len(elements)} elements")

# Test change detection
old_elements = parser.parse_file('old_version.py')
new_elements = parser.parse_file('new_version.py')
changes = parser.analyze_changes(old_elements, new_elements)
print(f"Detected {len(changes)} changes")
```

## Performance Considerations

### Optimization Guidelines

1. **PR Size Limits**: Keep analysis under 500-1000 files for reasonable performance
2. **Timeout Management**: Set appropriate timeouts (5-10 minutes) for analysis
3. **Caching**: AST parsing results cached for repeated analysis
4. **Parallel Processing**: Multiple file analysis can be parallelized
5. **Resource Limits**: Container resource limits prevent runaway analysis

### Performance Metrics

The agent tracks performance metrics:

```python
# Access performance metrics
metrics = reviewer.get_metrics()
print(f"Average review time: {metrics['average_review_time']} seconds")
print(f"Reviews completed: {metrics['reviews_completed']}")
print(f"ADRs generated: {metrics['adrs_generated']}")
```

## Security Considerations

### Execution Security

- **Container Isolation**: All analysis runs in isolated containers
- **Resource Limits**: CPU, memory, and network constraints
- **File System Access**: Limited to repository contents
- **Network Access**: Only GitHub API endpoints

### Data Privacy

- **No Data Persistence**: Analysis results stored temporarily in containers
- **GitHub API**: Only repository data accessed, no personal information
- **Audit Logging**: All operations logged for security review

## Future Enhancements

### Planned Features

1. **Multi-Language Support**: Additional language parsers (Go, Rust, Java)
2. **ML-Based Pattern Recognition**: Machine learning for pattern detection
3. **Integration Metrics**: Quantitative architecture quality metrics
4. **Custom Pattern Definitions**: User-defined architectural patterns
5. **Dashboard Integration**: Web interface for review history and metrics

### Extension Points

- **Custom AST Parsers**: Implement language-specific parsers
- **Pattern Detectors**: Add custom architectural pattern recognition
- **Documentation Templates**: Customize documentation section templates
- **ADR Templates**: Define custom ADR formats
- **Integration Hooks**: Custom webhooks for external systems

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd gadugi

# Create development environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest tests/agents/system_design_reviewer/ -v
```

### Adding New Features

1. **AST Parsers**: Implement `ASTParser` interface for new languages
2. **Pattern Detectors**: Add patterns to parser configuration
3. **Documentation Sections**: Add section handlers to `DocumentationManager`
4. **ADR Types**: Add decision types to `ADRGenerator`
5. **Integration Points**: Extend shared module usage

### Code Standards

- **Type Hints**: All functions must have type annotations
- **Documentation**: Comprehensive docstrings for all public methods
- **Testing**: >80% test coverage for new features
- **Code Quality**: Pass linting (black, flake8, mypy)
- **Performance**: Analysis should complete within 5 minutes

---

*This integration guide was generated as part of the System Design Review Agent implementation.*
*For support, create an issue in the repository or contact the development team.*
