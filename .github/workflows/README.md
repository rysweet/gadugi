# GitHub Actions Integration for Gadugi AI Agents

This directory contains GitHub Actions workflows and configurations for automated AI agent invocation based on repository events.

## 🚀 Quick Start

### Prerequisites

1. **Repository Setup**: Ensure Gadugi agents are installed in your `.claude/agents/` directory
2. **Memory Manager**: The `simple_memory_cli.py` should be available in `.github/memory-manager/`
3. **GitHub Token**: Standard `GITHUB_TOKEN` is sufficient for basic operations

### Basic Usage

The integration provides three main workflows out of the box:

1. **Label-Triggered Agents** (`label-triggered-agent.yml`)
2. **PR Review Agents** (`pr-review-agent.yml`) 
3. **Issue Triage Agents** (`issue-triage-agent.yml`)

## 📋 Available Workflows

### 1. Label-Triggered Agent Invocation

**File**: `.github/workflows/label-triggered-agent.yml`

**Triggers**: When specific labels are applied to issues or PRs

**Supported Labels**:
- `ai-agent:code-reviewer` → Invokes code-reviewer agent
- `ai-agent:workflow-master` → Invokes workflow-master agent
- `ai-agent:orchestrator` → Invokes orchestrator-agent
- `needs-review` → Invokes code-reviewer (alias)
- `needs-triage` → Invokes orchestrator-agent (alias)
- `bug-analysis` → Invokes code-reviewer for bug analysis
- `feature-enhancement` → Invokes workflow-master

**Example Usage**:
```bash
# Apply label to invoke code reviewer
gh issue edit 123 --add-label "ai-agent:code-reviewer"

# Apply label for issue triage
gh issue edit 456 --add-label "needs-triage"
```

### 2. PR Ready for Review Agent

**File**: `.github/workflows/pr-review-agent.yml`

**Triggers**: 
- When PR is marked ready for review
- When PR is opened (if not draft)
- When a review requests changes

**Features**:
- Automatic agent selection based on PR size and content
- File type analysis (Python, Markdown, YAML)
- Priority assignment based on PR characteristics
- Comprehensive review request comments

**Agent Selection Logic**:
- **Small PRs** (< 5 files): `code-reviewer`
- **Large PRs** (> 20 files): `orchestrator-agent`
- **Feature PRs** (title starts with "feat"): `workflow-master`
- **Bug fixes** (title starts with "fix"): `code-reviewer`
- **Documentation** (title starts with "docs"): `prompt-writer`

### 3. Issue Triage Agent

**File**: `.github/workflows/issue-triage-agent.yml`

**Triggers**:
- When new issues are opened
- When issues are reopened
- Scheduled runs every 6 hours for batch triage

**Features**:
- Content analysis for automatic categorization
- Label application based on issue patterns
- Priority assignment
- Batch processing of untriaged issues

**Categories Detected**:
- **Bugs**: Keywords like "error", "crash", "broken"
- **Features**: Keywords like "feature", "enhancement", "add"
- **Documentation**: Keywords like "docs", "readme", "guide"
- **Questions**: Keywords like "question", "help", "how to"
- **Performance**: Keywords like "slow", "performance", "optimization"

## 🔧 Reusable Action

### Invoke Agent Action

**Location**: `.github/actions/invoke-agent/action.yml`

A reusable action that can be used in custom workflows to invoke Gadugi agents.

**Usage Example**:
```yaml
- name: Invoke Custom Agent
  uses: ./.github/actions/invoke-agent
  with:
    agent: "code-reviewer"
    scenario: "security-analysis"
    priority: "high"
    github-token: ${{ secrets.GITHUB_TOKEN }}
    target-type: "pull_request"
    target-number: "123"
    auto-comment: "true"
```

**Parameters**:
- `agent` (required): Agent name (e.g., "code-reviewer", "workflow-master")
- `scenario` (required): Scenario context (e.g., "pr-review", "issue-triage")
- `priority` (optional): Priority level ("high", "medium", "low")
- `target-type` (required): Type of target ("issue", "pull_request", "repository")
- `target-number` (optional): Issue or PR number
- `auto-comment` (optional): Whether to create automatic comments

## 📝 Configuration Templates

### Custom Workflow Template

**Location**: `.github/workflows/templates/custom-agent-invocation.yml`

A template for creating custom agent invocation workflows tailored to your repository's needs.

### Configuration File

**Location**: `.github/workflows/templates/agent-config.yml`

A comprehensive configuration template showing all available options:
- Label-to-agent mapping
- Scenario definitions
- Priority rules
- Memory section mapping
- Team assignment rules

## 🎯 Example Scenarios

### Scenario 1: Invoke Agent When Label is Applied

```yaml
# In your workflow file
on:
  issues:
    types: [labeled]

# When someone applies the "ai-agent:code-reviewer" label
# The code-reviewer agent will be invoked automatically
```

**Usage**:
1. Apply label: `gh issue edit 123 --add-label "ai-agent:code-reviewer"`
2. Workflow triggers automatically
3. Agent analyzes the issue and provides feedback

### Scenario 2: PR Ready for Review

```yaml
# Automatically triggered when PR is ready
on:
  pull_request:
    types: [ready_for_review]

# Agent selection based on PR characteristics:
# - Large PRs: orchestrator-agent
# - Feature PRs: workflow-master  
# - Bug fixes: code-reviewer
```

**Usage**:
1. Create PR as draft
2. Mark as "Ready for review"
3. Appropriate agent automatically analyzes and comments

### Scenario 3: Issue Triage

```yaml
# Triggered on new issues and scheduled runs
on:
  issues:
    types: [opened]
  schedule:
    - cron: '0 */6 * * *'

# Automatic categorization and labeling based on content
```

**Usage**:
1. User creates new issue
2. System automatically analyzes content
3. Appropriate labels applied
4. Relevant agent provides initial triage

## 🔧 Advanced Configuration

### Custom Agent Selection

Create your own logic for agent selection:

```yaml
- name: Custom Agent Selection
  run: |
    if [[ "${{ github.event.issue.title }}" =~ security ]]; then
      echo "agent=code-reviewer" >> $GITHUB_OUTPUT
      echo "scenario=security-analysis" >> $GITHUB_OUTPUT
    elif [[ "${{ github.event.issue.body }}" =~ performance ]]; then
      echo "agent=orchestrator-agent" >> $GITHUB_OUTPUT
      echo "scenario=performance-investigation" >> $GITHUB_OUTPUT
    fi
```

### Memory Integration

All workflows integrate with the Gadugi memory system:

```yaml
- name: Update Agent Memory
  run: |
    cd .github/memory-manager
    python simple_memory_cli.py update "Context for agent" \
      --section current-goals \
      --agent GitHubActions \
      --priority high \
      --related "#${{ github.event.issue.number }}"
```

### Team Assignment

Configure automatic team assignment based on content:

```yaml
- name: Auto-assign Teams
  if: contains(github.event.issue.labels.*.name, 'security')
  run: |
    gh issue edit ${{ github.event.issue.number }} \
      --add-assignee security-team
```

## 🛠️ Available Agents

The workflows can invoke any of the Gadugi agents:

- **code-reviewer**: Code analysis, security review, bug investigation
- **workflow-master**: Feature development, workflow orchestration
- **orchestrator-agent**: Complex coordination, large issue/PR management
- **prompt-writer**: Documentation, guide creation, prompt development
- **agent-manager**: Agent synchronization and management
- **task-analyzer**: Task dependency analysis
- **worktree-manager**: Git worktree management
- **execution-monitor**: Parallel execution monitoring

## 📊 Monitoring and Logging

### Workflow Logs

Each workflow provides comprehensive logging:
- Agent selection reasoning
- Context analysis results
- Memory update status
- Success/failure indicators

### Memory Tracking

All agent invocations are recorded in the memory system:
- Timestamp and context
- Agent and scenario information
- Related issues/PRs
- Results and outcomes

### GitHub Integration

Workflows create informative comments on issues/PRs:
- Agent selection explanation
- Processing instructions
- Manual invocation commands
- Status updates

## 🔒 Security Considerations

### Token Permissions

The workflows use standard `GITHUB_TOKEN` with these permissions:
- `issues: write` - Create comments, apply labels
- `pull-requests: write` - Create reviews, comments
- `contents: read` - Access repository content

### Memory Security

- Memory updates are logged and tracked
- Only repository collaborators can trigger workflows
- Sensitive data is not stored in memory

### Rate Limiting

Workflows include rate limiting to prevent abuse:
- Maximum issues processed per batch run
- Circuit breaker patterns for failure handling
- Exponential backoff for API failures

## 🚀 Getting Started

1. **Copy workflows** to your `.github/workflows/` directory
2. **Customize configuration** in templates as needed
3. **Test with labels** - apply `ai-agent:code-reviewer` to an issue
4. **Monitor logs** in GitHub Actions tab
5. **Refine configuration** based on your workflow needs

## 📞 Support

For issues or questions:
1. Check workflow logs in GitHub Actions
2. Review memory system status with `simple_memory_cli.py status`
3. Consult Gadugi documentation for agent-specific help
4. Open an issue with the `ai-agent:prompt-writer` label for documentation help

---

*🤖 This integration enables seamless AI-assisted development workflows through GitHub Actions automation*