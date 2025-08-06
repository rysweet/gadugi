# Gadugi Event Service Guide

The Gadugi Event Service transforms manual agent invocation into a fully automated, event-driven system. This guide covers installation, configuration, and usage of the event-driven agent invocation system.

## Overview

The Event Service provides:

- **GitHub Webhook Integration**: Automatic agent invocation on GitHub events
- **Local Event Support**: Unix socket for local event submission
- **Polling Fallback**: GitHub API polling when webhooks aren't available
- **Flexible Event Filtering**: Pattern matching and complex filtering rules
- **Multiple Agent Invocation Methods**: Claude CLI, direct, and subprocess execution
- **Comprehensive Configuration**: YAML-based configuration with environment overrides

## Quick Start

### 1. Installation

Install the Gadugi Event Service using the Claude agent:

```bash
claude /agent:gadugi

Install Gadugi event service with default configuration
```

Or manually using the CLI:

```bash
# Install with interactive setup
gadugi install

# Install with GitHub token
gadugi install --github-token ghp_your_token_here

# Install without webhook setup
gadugi install --no-webhook
```

### 2. Start the Service

```bash
gadugi start
```

The service will:
- Start HTTP server for webhooks on port 8080
- Create Unix socket for local events
- Begin GitHub API polling (if configured)
- Load and activate event handlers

### 3. Verify Installation

```bash
# Check service status
gadugi status

# View service logs
gadugi logs --tail

# List configured handlers
gadugi handler list
```

## Configuration

### Configuration File

The service uses `~/.gadugi/config.yaml` for configuration:

```yaml
service_name: gadugi-event-service
bind_address: 127.0.0.1
bind_port: 8080
socket_path: ~/.gadugi/events.sock
poll_interval_seconds: 300
github_token: ghp_your_token_here
webhook_secret: your_webhook_secret

log_config:
  level: INFO
  format: text
  output: file
  file_path: ~/.gadugi/logs/gadugi-service.log
  enable_audit: true
  audit_file_path: ~/.gadugi/logs/gadugi-audit.log

handlers:
  - name: new-issue-workflow
    enabled: true
    priority: 100
    timeout_seconds: 600
    async: false
    filter:
      event_types:
        - github.issues.opened
      github_filter:
        webhook_events:
          - issues
        actions:
          - opened
    invocation:
      agent_name: workflow-manager
      method: claude_cli
      prompt_template: |
        New issue #{number}: {title}
        
        Repository: {repository}
        Author: {actor}
        Labels: {labels}
        
        {body}
        
        Analyze and create workflow for this issue.

  - name: pr-code-review
    enabled: true
    priority: 90
    timeout_seconds: 900
    async: true
    filter:
      event_types:
        - github.pull_request.opened
        - github.pull_request.synchronize
      github_filter:
        webhook_events:
          - pull_request
        actions:
          - opened
          - synchronize
    invocation:
      agent_name: code-reviewer
      method: claude_cli
      prompt_template: |
        Review PR #{number}: {title}
        
        Repository: {repository}
        Author: {actor}
        Status: {state}
        
        Perform comprehensive code review.

  - name: main-merge-memory-update
    enabled: true
    priority: 80
    timeout_seconds: 300
    async: false
    filter:
      event_types:
        - github.push
      github_filter:
        webhook_events:
          - push
        refs:
          - refs/heads/main
    invocation:
      agent_name: memory-manager
      method: claude_cli
      prompt_template: |
        Update Memory.md after merge to main: {ref}
        
        Repository: {repository}
        Synchronize project memory with latest changes.
```

### Environment Variables

Override configuration with environment variables:

```bash
export GADUGI_BIND_PORT=8080
export GADUGI_GITHUB_TOKEN=ghp_your_token_here
export GADUGI_WEBHOOK_SECRET=your_secret
export GADUGI_POLL_INTERVAL=300
export GADUGI_LOG_LEVEL=DEBUG
```

### Interactive Configuration

Use the interactive configuration editor:

```bash
gadugi config --edit
```

## Event Handlers

### Handler Structure

Each event handler consists of:

- **Filter**: Determines which events trigger the handler
- **Invocation**: Specifies how to execute the agent
- **Configuration**: Priority, timeout, async execution settings

### Event Filtering

#### Event Type Patterns

```yaml
filter:
  event_types:
    - github.*                    # All GitHub events
    - github.issues.*            # All issue events
    - github.pull_request.opened # Specific PR events
    - local.file_changed         # Local events
    - agent.*.completed          # Agent completion events
```

#### GitHub-Specific Filtering

```yaml
filter:
  github_filter:
    repositories:               # Specific repositories
      - owner/repo1
      - owner/repo2
    webhook_events:             # GitHub webhook event types
      - issues
      - pull_request
      - push
    actions:                    # GitHub actions
      - opened
      - closed
      - synchronize
    labels:                     # Issue/PR labels (any match)
      - bug
      - urgent
    actors:                     # GitHub users
      - dependabot[bot]
      - renovate[bot]
    refs:                       # Git references (supports patterns)
      - refs/heads/main
      - refs/heads/feature/*
    milestones:                 # Milestone names
      - v1.0.0
      - Sprint 1
```

#### Metadata Filtering

```yaml
filter:
  metadata_match:
    priority: high
    team: backend
    environment: production
```

### Agent Invocation Methods

#### Claude CLI (Recommended)

```yaml
invocation:
  agent_name: workflow-manager
  method: claude_cli
  prompt_template: |
    Handle event: {event_type}
    
    Event details:
    - Repository: {repository}
    - Action: {action}
    - Title: {title}
  parameters:
    timeout: "300"
  environment:
    CUSTOM_VAR: "value"
  working_directory: /path/to/project
```

#### Direct Python (Advanced)

```yaml
invocation:
  agent_name: my_custom_agent
  method: direct
  parameters:
    config_file: /path/to/config.yaml
```

#### Subprocess

```yaml
invocation:
  agent_name: /path/to/script.sh
  method: subprocess
  parameters:
    arg1: value1
  environment:
    SCRIPT_CONFIG: /path/to/config
```

### Template Variables

Event handlers can use these template variables in prompts:

#### Common Variables
- `{event_id}` - Unique event identifier
- `{event_type}` - Event type (e.g., github.issues.opened)
- `{timestamp}` - Event timestamp
- `{source}` - Event source (github, local, agent)

#### GitHub Event Variables
- `{repository}` - Repository name (owner/repo)
- `{number}` - Issue/PR number
- `{action}` - GitHub action (opened, closed, etc.)
- `{actor}` - GitHub user who triggered event
- `{title}` - Issue/PR title
- `{body}` - Issue/PR body content
- `{state}` - Current state (open, closed, merged)
- `{labels}` - Comma-separated labels
- `{assignees}` - Comma-separated assignees
- `{milestone}` - Milestone name
- `{ref}` - Git reference (for push events)

#### Local Event Variables
- `{event_name}` - Local event name
- `{working_directory}` - Working directory
- `{files_changed}` - Comma-separated changed files

#### Agent Event Variables
- `{agent_name}` - Agent that generated the event
- `{task_id}` - Task identifier
- `{phase}` - Current phase
- `{status}` - Event status
- `{message}` - Event message

## GitHub Integration

### Webhook Setup

#### Automatic Setup

```bash
# Auto-detect repository and create webhook
gadugi webhook setup

# Specify repository
gadugi webhook setup --repo owner/repository
```

#### Manual Setup

1. Go to repository Settings → Webhooks
2. Click "Add webhook"
3. Set Payload URL: `http://your-server:8080/webhook/github`
4. Set Content type: `application/json`
5. Set Secret: Your webhook secret from config
6. Select events: Issues, Pull requests, Pushes
7. Click "Add webhook"

#### Webhook Management

```bash
# List webhooks
gadugi webhook list --repo owner/repo

# Test webhook
gadugi webhook test --repo owner/repo --hook-id 12345

# Delete webhook
gadugi webhook delete --repo owner/repo --hook-id 12345
```

### API Polling (Fallback)

When webhooks aren't available, the service polls GitHub API:

```yaml
poll_interval_seconds: 300  # Poll every 5 minutes
github_token: ghp_token     # Required for polling
```

## Local Events

### Sending Local Events

#### Via CLI

```bash
# Simple event
gadugi send local.test

# Event with data
gadugi send local.file_changed --data '{"files": ["file1.py", "file2.py"]}'

# Event from file
gadugi send local.deployment --file event_data.json
```

#### Via Unix Socket (Programmatic)

```python
import json
import socket
from gadugi.event_service.events import create_local_event

# Create event
event = create_local_event(
    event_name="file_changed",
    working_directory="/path/to/project",
    files_changed=["src/main.py", "tests/test_main.py"]
)

# Send via socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("~/.gadugi/events.sock")
sock.send(event.to_json().encode('utf-8'))

# Read response
response = sock.recv(1024)
result = json.loads(response.decode('utf-8'))
print(f"Event status: {result['status']}")

sock.close()
```

### Local Event Handlers

```yaml
handlers:
  - name: file-change-handler
    filter:
      event_types:
        - local.file_changed
      metadata_match:
        file_type: python
    invocation:
      agent_name: test-writer
      method: claude_cli
      prompt_template: |
        Files changed: {files_changed}
        
        Generate tests for the modified Python files.
```

## Service Management

### Systemd Service (Linux)

```bash
# Install as system service
sudo gadugi install --system

# Manage with systemctl
sudo systemctl start gadugi
sudo systemctl enable gadugi
sudo systemctl status gadugi
```

### Launchd Service (macOS)

```bash
# Install as user service
gadugi install --user

# Manage with launchctl
launchctl load ~/Library/LaunchAgents/com.gadugi.event-service.plist
launchctl start com.gadugi.event-service
```

### Manual Service Management

```bash
# Start service
gadugi start

# Stop service
gadugi stop

# Restart service
gadugi restart

# Check status
gadugi status

# View logs
gadugi logs --tail
gadugi logs --lines 100
```

## Advanced Usage

### Custom Event Handlers

Create custom handlers for specific workflows:

```yaml
handlers:
  - name: security-vulnerability-handler
    priority: 200  # High priority
    filter:
      event_types:
        - github.issues.opened
      github_filter:
        labels:
          - security
          - vulnerability
    invocation:
      agent_name: security-analyzer
      method: claude_cli
      timeout_seconds: 1200  # Extended timeout
      prompt_template: |
        SECURITY ALERT: {title}
        
        Repository: {repository}
        Reporter: {actor}
        
        {body}
        
        Perform immediate security analysis and create response plan.

  - name: dependency-update-handler
    filter:
      event_types:
        - github.pull_request.opened
      github_filter:
        actors:
          - dependabot[bot]
          - renovate[bot]
    invocation:
      agent_name: dependency-reviewer
      method: claude_cli
      prompt_template: |
        Dependency update PR: {title}
        
        Review and validate dependency changes.
        Check for breaking changes and security issues.
```

### Event Chaining

Chain events by having agents generate new events:

```python
# In an agent, generate follow-up event
from gadugi.event_service.events import create_agent_event

# Create follow-up event
follow_up = create_agent_event(
    agent_name="workflow-manager",
    task_id="task-123",
    phase="testing",
    status="completed",
    message="Implementation complete, starting tests"
)

# Send to local event service
# (This would trigger other handlers listening for agent.*.completed events)
```

### Conditional Logic

Use metadata for conditional handler execution:

```yaml
handlers:
  - name: production-deployment
    filter:
      event_types:
        - github.push
      github_filter:
        refs:
          - refs/heads/main
      metadata_match:
        environment: production
    invocation:
      agent_name: deployment-manager
      method: claude_cli

  - name: staging-deployment
    filter:
      event_types:
        - github.push
      github_filter:
        refs:
          - refs/heads/develop
      metadata_match:
        environment: staging
    invocation:
      agent_name: deployment-manager
      parameters:
        target_env: staging
```

## Troubleshooting

### Service Issues

```bash
# Check service status
gadugi status

# View detailed logs
gadugi logs --tail

# Validate configuration
gadugi config --validate

# Test webhook connectivity
gadugi webhook test --repo owner/repo --hook-id 12345
```

### Common Problems

#### Service Won't Start

1. Check port availability:
   ```bash
   lsof -i :8080
   ```

2. Verify configuration:
   ```bash
   gadugi config --show
   gadugi config --validate
   ```

3. Check permissions:
   ```bash
   ls -la ~/.gadugi/
   ```

#### Webhooks Not Working

1. Verify webhook URL is accessible
2. Check webhook secret matches configuration
3. Review GitHub webhook delivery logs
4. Check service logs for webhook events

#### Agents Not Executing

1. Verify Claude CLI is installed and accessible
2. Check agent invocation configuration
3. Review agent execution logs
4. Test agent manually:
   ```bash
   claude /agent:workflow-manager
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Temporary debug mode
GADUGI_LOG_LEVEL=DEBUG gadugi start

# Or update configuration
gadugi config --edit
# Set log_config.level: DEBUG
```

## Security Considerations

### GitHub Token

- Use fine-grained personal access tokens
- Limit token scope to specific repositories
- Rotate tokens regularly
- Store securely (environment variables, not config files)

### Webhook Security

- Always use webhook secrets
- Verify webhook signatures
- Use HTTPS for webhook URLs
- Monitor webhook delivery logs

### Agent Execution

- Review agent code before enabling handlers
- Use timeouts to prevent runaway agents
- Monitor resource usage
- Consider running in containers for isolation

### Network Security

- Bind service to localhost unless external access needed
- Use firewall rules to restrict access
- Consider VPN for remote webhook access
- Monitor service logs for suspicious activity

## Best Practices

### Handler Design

1. **Specific Filters**: Use precise event filters to avoid unwanted triggers
2. **Idempotent Agents**: Ensure agents can be safely re-run
3. **Error Handling**: Include error recovery in agent logic
4. **Timeouts**: Set appropriate timeouts for different agent types
5. **Async Execution**: Use async for long-running agents

### Performance

1. **Handler Priority**: Set priorities to control execution order
2. **Resource Limits**: Monitor CPU and memory usage
3. **Log Rotation**: Configure log rotation to prevent disk issues
4. **Batch Processing**: Group related events when possible

### Monitoring

1. **Health Checks**: Regular status checks
2. **Log Analysis**: Monitor for errors and performance issues
3. **Metrics Collection**: Track handler execution times and success rates
4. **Alerting**: Set up alerts for service failures

This guide provides comprehensive coverage of the Gadugi Event Service. For additional help, consult the API documentation or create an issue in the project repository.