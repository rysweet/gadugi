## Code Review Memory - 2025-08-01

### PR #4: fix: enhance agent-manager hook deduplication and error handling

#### What I Learned
- Gadugi is a multi-agent Claude Code system with complex hook integration
- Claude Code hooks run in shell environments, NOT in Claude's agent context
- The `/agent:` syntax only works within Claude Code sessions, not in shell hooks
- The agent-manager uses Python scripts embedded in Markdown files for configuration
- The project uses comprehensive Python testing with subprocess execution for bash functions

#### Design Patterns Discovered
- **Embedded Scripts in Markdown**: Agent definitions contain executable bash/Python code blocks
- **Hook Deduplication Strategy**: Complex filtering logic to remove existing hooks before adding new ones
- **Graceful Degradation**: Shell scripts provide basic functionality when full agent features aren't available
- **JSON Validation and Recovery**: Robust error handling for corrupted settings files
- **Test Strategy**: Extracting and testing bash functions through subprocess execution

#### Architectural Insights
- Settings stored in `.claude/settings.json` with hooks configuration
- Shell scripts placed in `.claude/hooks/` for hook execution
- Agent configurations in `.claude/agents/` as Markdown files
- Test coverage focuses on integration testing through actual script execution
- Backup and recovery mechanisms for configuration files

#### Security Considerations
- No hardcoded credentials or sensitive data found
- Input validation present for JSON parsing
- File permissions properly set on executable scripts
- Backup files prevent data loss during updates

#### Patterns to Watch
- **Hook Syntax Limitations**: Remember hooks cannot use `/agent:` syntax directly
- **JSON Corruption Handling**: The invalid JSON recovery pattern is solid
- **Deduplication Logic**: Complex but necessary to prevent duplicate hook registration
- **Cross-platform Compatibility**: Uses `#\!/bin/sh` instead of bash for broader compatibility

#### Test Coverage Assessment
- Comprehensive test suite covering all major functionality
- Tests use realistic subprocess execution rather than mocks
- Edge cases well covered (invalid JSON, missing files, permission issues)
- All 7 test cases passing consistently
EOF < /dev/null