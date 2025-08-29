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

### Emergency Override (Use Sparingly)
```bash
# Set emergency override for direct git operations
export GADUGI_EMERGENCY_OVERRIDE=true
git commit -m "Critical hotfix - justification here"
unset GADUGI_EMERGENCY_OVERRIDE  # Always unset after use
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
- **Solution**: Use orchestrator workflow or emergency override with justification

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

### View Emergency Overrides
```bash
cat .claude/workflow-enforcement/emergency_overrides.log
```

## 🚨 Emergency Procedures

### Production Hotfix
1. Set emergency override: `export GADUGI_EMERGENCY_OVERRIDE=true`
2. Make minimal changes
3. Commit with clear justification
4. Unset override: `unset GADUGI_EMERGENCY_OVERRIDE`
5. Schedule proper workflow review

### Disable Enforcement Temporarily
```bash
# Disable git hooks temporarily
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Re-enable when ready
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

---
Remember: The workflow exists to protect code quality and ensure proper testing!
