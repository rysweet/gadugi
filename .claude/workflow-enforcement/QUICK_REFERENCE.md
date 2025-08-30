# Workflow Enforcement Quick Reference

## 🚀 Common Commands

### Validate Task Compliance
```bash
# Check if your task needs orchestrator
.claude/workflow-enforcement/validate-workflow.py --task "fix user authentication"

# Check with specific files
.claude/workflow-enforcement/validate-workflow.py --task "update config" --files config.json settings.py
```

### Use Orchestrator (Required for Code Changes)
```bash
cd /Users/ryan/src/gadugi5/gadugi
python .claude/orchestrator/main.py --task "your task description"
```

### Monitoring and Compliance
```bash
# Start real-time monitoring
.claude/workflow-enforcement/compliance-monitor.py --start

# Generate compliance report
.claude/workflow-enforcement/compliance-monitor.py --report

# Immediate compliance check
.claude/workflow-enforcement/compliance-monitor.py --check
```

### NO EMERGENCY OVERRIDES
```bash
# ⛔ EMERGENCY OVERRIDES ARE STRICTLY FORBIDDEN
# All code changes MUST go through the orchestrator workflow
# NO EXCEPTIONS - If blocked, fix the underlying problem
```

## 🎯 Decision Matrix

| Task Type | Use Orchestrator? | Why |
|-----------|-------------------|-----|
| Fix bugs | ✅ YES | Code changes need testing |
| Add features | ✅ YES | New code needs validation |
| Update config | ✅ YES | Config affects system behavior |
| Read files | ❌ NO | No modifications made |
| Code analysis | ❌ NO | Read-only operation |
| Answer questions | ❌ NO | Informational only |

## 📋 The 11-Phase Workflow

1. **Task Validation** - Validate requirements and scope
2. **Environment Setup** - Prepare development environment
3. **Dependency Analysis** - Analyze impact and dependencies
4. **Worktree Creation** - Create isolated development branch
5. **Implementation** - Execute the actual code changes
6. **Testing** - Run comprehensive test suites
7. **Quality Gates** - Type checking, linting, security scans
8. **Documentation** - Update relevant documentation
9. **Review** - Code review and validation
10. **Integration** - Merge to target branch
11. **Cleanup** - Clean up temporary resources

## 🔧 Troubleshooting

### "Workflow violation detected"
- **Cause**: Attempting code changes without orchestrator
- **Solution**: Use `python .claude/orchestrator/main.py --task "your task"`

### "Pre-commit hook blocked commit"
- **Cause**: Direct git commit without orchestrator context
- **Solution**: Use orchestrator workflow - NO EXCEPTIONS

### "Orchestrator not found"
- **Cause**: Missing orchestrator setup
- **Solution**: Check that `.claude/orchestrator/main.py` exists

## 📊 Monitoring

### View Recent Activity
```bash
tail -f .claude/workflow-enforcement/workflow_activity.log
```

### Check Compliance Status
```bash
python .claude/workflow-enforcement/workflow-checker.py --report
```

## 🚨 NO EMERGENCY PROCEDURES

### All Changes Must Use Workflow
- **NO EXCEPTIONS**: Every change goes through orchestrator
- **NO OVERRIDES**: If blocked, fix the problem
- **NO BYPASSES**: Workflow enforcement is mandatory
- **If stuck**: Debug and fix the underlying issue

### Proper Workflow Usage
```bash
# Always use orchestrator for code changes
python .claude/orchestrator/main.py --task "your task description"
```

---
Remember: The workflow exists to protect code quality and ensure proper testing!
