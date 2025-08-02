# GitHub Actions Agent Integration Examples

This document provides practical examples of how to use the GitHub Actions integration with Gadugi AI agents.

## 🎯 Example 1: Label-Triggered Code Review

### Scenario
A team member wants an AI code review on a specific issue or PR.

### Steps
1. **Apply Label**: Add the `ai-agent:code-reviewer` label to an issue or PR
   ```bash
   gh issue edit 123 --add-label "ai-agent:code-reviewer"
   # or
   gh pr edit 456 --add-label "ai-agent:code-reviewer"
   ```

2. **Automatic Trigger**: The workflow `label-triggered-agent.yml` automatically triggers

3. **Agent Invocation**: The system:
   - Analyzes the target (issue/PR)
   - Updates agent memory with context
   - Posts a comment with agent instructions
   - Provides manual commands if needed

### Expected Output
```markdown
🤖 **Gadugi Agent Invocation**

**Agent: code-reviewer | Scenario: code-review | Priority: medium | Target: issue #123**

### 🎯 Agent Assignment
- **Agent:** `code-reviewer`
- **Scenario:** `code-review`
- **Priority:** MEDIUM
- **Trigger:** GitHub Actions automation

### 🚀 Agent Command
The following command has been prepared for agent processing:

```
/agent:code-reviewer

Context: GitHub Actions automated invocation
Target: issue #123
Scenario: code-review
Priority: medium
Repository: rysweet/gadugi
Triggered by: rysweet
Workflow: Label Triggered Agent Invocation

Please analyze and process this issue based on the code-review scenario.
```
```

## 🎯 Example 2: PR Ready for Review

### Scenario
A developer creates a PR and marks it ready for review.

### Steps
1. **Create PR**: Developer creates a pull request
2. **Mark Ready**: Convert from draft or mark as ready for review
3. **Automatic Analysis**: The system analyzes:
   - Number of files changed
   - Lines added/deleted
   - File types (Python, Markdown, YAML)
   - PR title patterns

### Agent Selection Logic
```yaml
# Small PR (< 5 files, < 100 lines)
Agent: code-reviewer
Scenario: quick-review

# Large PR (> 20 files, > 500 lines)  
Agent: orchestrator-agent
Scenario: large-pr-coordination

# Feature PR (title: "feat:", "feature:")
Agent: workflow-master
Scenario: feature-review

# Bug Fix PR (title: "fix:", "bug:")
Agent: code-reviewer  
Scenario: bugfix-review
```

### Expected Output
The PR will receive a comprehensive review comment with:
- PR analysis (files, lines, types)
- Selected agent and reasoning
- Agent command for processing
- Review checklist
- Manual commands if needed

## 🎯 Example 3: Issue Triage

### Scenario
New issues are automatically triaged and categorized.

### Automatic Triggers
1. **New Issue**: When an issue is opened
2. **Batch Processing**: Every 6 hours for untriaged issues

### Content Analysis Examples

**Bug Report Detection**:
```
Title: "Login form crashes on submit"
Body: "Steps to reproduce: 1. Enter credentials 2. Click submit 3. Application crashes"

Result:
- Category: bug
- Labels: bug, needs-investigation  
- Agent: code-reviewer
- Priority: high
```

**Feature Request Detection**:
```
Title: "Add dark mode support"
Body: "It would be great if the app supported dark mode theme"

Result:
- Category: feature
- Labels: enhancement, feature-request
- Agent: workflow-master
- Priority: medium
```

**Documentation Issue**:
```
Title: "README installation instructions unclear"
Body: "The setup guide is missing dependencies information"

Result:
- Category: documentation
- Labels: documentation, good-first-issue
- Agent: prompt-writer
- Priority: medium
```

## 🎯 Example 4: Custom Workflow

### Scenario
Create a custom workflow for security-related issues.

### Implementation
```yaml
# .github/workflows/security-agent.yml
name: Security Issue Handler

on:
  issues:
    types: [labeled]

jobs:
  security-analysis:
    if: contains(github.event.label.name, 'security')
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Invoke Security Agent
      uses: ./.github/actions/invoke-agent
      with:
        agent: "code-reviewer"
        scenario: "security-analysis"
        priority: "high"
        github-token: ${{ secrets.GITHUB_TOKEN }}
        target-type: "issue"
        target-number: ${{ github.event.issue.number }}
        context-data: |
          {
            "security_level": "high",
            "requires_immediate_attention": true,
            "escalation_needed": true
          }
```

### Usage
```bash
# Apply security label to trigger specialized workflow
gh issue edit 789 --add-label "security"
```

## 🎯 Example 5: Manual Agent Invocation

### Scenario
Manually trigger agent processing using workflow dispatch.

### Implementation
Use the custom template workflow with manual triggers:

```bash
# Trigger via GitHub CLI
gh workflow run "Custom Agent Invocation" \
  -f agent=orchestrator-agent \
  -f target_type=repository \
  -f scenario=project-analysis

# Or via GitHub web interface
# Go to Actions → Custom Agent Invocation → Run workflow
```

## 🔧 Testing Your Integration

### Test Checklist

1. **Label Test**:
   ```bash
   # Create test issue
   gh issue create --title "Test Issue for AI Review" --body "This is a test"
   
   # Apply agent label
   gh issue edit <issue_number> --add-label "ai-agent:code-reviewer"
   
   # Check Actions tab for workflow execution
   ```

2. **PR Test**:
   ```bash
   # Create feature branch
   git checkout -b test-pr-automation
   
   # Make changes and push
   echo "Test change" >> README.md
   git add README.md
   git commit -m "feat: test PR automation"
   git push origin test-pr-automation
   
   # Create PR
   gh pr create --title "feat: Test PR Automation" --body "Testing automated agent invocation"
   
   # Mark ready for review (if created as draft)
   gh pr ready <pr_number>
   ```

3. **Issue Triage Test**:
   ```bash
   # Test bug report
   gh issue create --title "Application crashes on startup" \
     --body "Steps to reproduce: 1. Start app 2. Immediate crash. Error message: 'Cannot find module'"
   
   # Test feature request  
   gh issue create --title "Add export to CSV feature" \
     --body "It would be helpful to export data to CSV format for analysis"
   ```

### Monitoring Results

1. **GitHub Actions**: Check the Actions tab for workflow execution logs
2. **Issue/PR Comments**: Look for automated agent invocation comments
3. **Memory System**: Use `simple_memory_cli.py status` to check memory updates
4. **Labels**: Verify automatic label application on issues

## 🛠️ Troubleshooting

### Common Issues

1. **Workflow Not Triggering**:
   - Check if workflow files are in `main` branch
   - Verify YAML syntax with `python -c "import yaml; yaml.safe_load(open('file.yml'))"`
   - Ensure repository has Actions enabled

2. **Agent Not Found**:  
   - Verify agent files exist in `.claude/agents/`
   - Check agent name spelling in workflow configuration
   - Review `manifest.yaml` for available agents

3. **Memory Updates Failing**:
   - Check if `simple_memory_cli.py` exists in `.github/memory-manager/`
   - Verify `requirements.txt` dependencies are installed
   - Check GitHub token permissions

4. **YAML Syntax Errors**:
   - Use the test script: `python test_github_actions_integration.py`
   - Validate individual files with YAML parsers
   - Check for indentation and special character issues

### Debug Commands

```bash
# Validate workflow syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/label-triggered-agent.yml'))"

# Test memory manager
cd .github/memory-manager
python simple_memory_cli.py status

# List available agents
ls -la .claude/agents/

# Check workflow history
gh run list --workflow="Label Triggered Agent Invocation"
```

## 📊 Performance Considerations

### Rate Limits
- GitHub API: 5,000 requests/hour per repository
- Workflow runs: 1,000 API requests per hour per repository
- Concurrent jobs: 20 concurrent jobs per repository

### Optimization Tips
1. **Batch Processing**: Use scheduled runs for bulk operations
2. **Conditional Execution**: Use `if` conditions to avoid unnecessary runs  
3. **Caching**: Cache dependencies between workflow runs
4. **Circuit Breakers**: Implement failure handling to prevent cascading issues

### Monitoring Metrics
- Workflow execution time
- Success/failure rates
- Agent invocation frequency
- Memory system usage
- API rate limit consumption

---

*🚀 This integration enables powerful AI-assisted development workflows while maintaining flexibility and control over when and how agents are invoked.*