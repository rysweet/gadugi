# Workflow Enforcement Documentation

## 🚨 CRITICAL: Mandatory Workflow for Code Changes

**ALL CODE CHANGES MUST USE THE ORCHESTRATOR WORKFLOW**

### ⚡ Quick Decision Matrix

| Task Type | Files Modified? | Use Orchestrator? | Reason |
|-----------|----------------|-------------------|---------|
| Fix bugs | ✅ Yes | ✅ **REQUIRED** | Code changes need proper testing |
| Add features | ✅ Yes | ✅ **REQUIRED** | New code needs full validation |
| Refactor code | ✅ Yes | ✅ **REQUIRED** | Changes need impact analysis |
| Update config | ✅ Yes | ✅ **REQUIRED** | Config changes affect system |
| Write tests | ✅ Yes | ✅ **REQUIRED** | Tests are code changes |
| Read/analyze | ❌ No | ❌ Direct OK | No modifications made |
| Answer questions | ❌ No | ❌ Direct OK | Informational only |

### 🎯 The 11-Phase Workflow

When using the orchestrator, all tasks follow these mandatory phases:

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

### 🔍 What Constitutes a "Code Change"?

**Code changes include:**
- Modifying any source files (`.py`, `.js`, `.ts`, `.go`, etc.)
- Creating new files or directories
- Deleting files or directories
- Updating configuration files (`.json`, `.yaml`, `.yml`)
- Modifying documentation files (`.md`, `.txt`)
- Changing shell scripts (`.sh`, `.bash`)
- Installing/updating dependencies
- Making git operations (commits, merges, branches)

**Not code changes:**
- Reading existing files
- Analyzing code structure
- Answering questions about code
- Generating reports
- Searching/exploring codebase

### 🚫 Common Workflow Violations

#### ❌ Violation Example 1: Direct File Editing
```bash
# WRONG - Direct file modification
Edit file: /path/to/script.py
```

✅ **Correct Approach:**
```bash
# Use orchestrator for code changes
python .claude/orchestrator/main.py --task "Fix script.py functionality" --files "script.py"
```

#### ❌ Violation Example 2: Bypassing Testing
```bash
# WRONG - Making changes without testing
Modify multiple files without running tests
```

✅ **Correct Approach:**
```bash
# Orchestrator automatically runs testing phase
# All changes go through comprehensive validation
```

#### ❌ Violation Example 3: Direct Git Operations
```bash
# WRONG - Direct git commits
git add . && git commit -m "Quick fix"
```

✅ **Correct Approach:**
```bash
# Orchestrator handles git operations in Integration phase
# Ensures proper commit messages and branch management
```

### 🛡️ Enforcement Mechanisms

The system implements multiple enforcement layers:

1. **Pre-execution Validation** - Checks before task execution
2. **Real-time Monitoring** - Watches for workflow violations
3. **Compliance Logging** - Records all executions and violations
4. **Automated Warnings** - Alerts when violations detected
5. **Graceful Redirection** - Suggests correct workflow approach

### 🚨 Violation Response Levels

#### Level 1: Warning
- First-time violation
- Educational message displayed
- Execution continues with warning logged

#### Level 2: Strong Warning
- Repeated violations
- Execution paused for confirmation
- User must acknowledge workflow requirement

#### Level 3: Enforcement
- Persistent violations
- Automatic redirection to orchestrator
- Override requires justification

### 🔓 Emergency Override

In rare cases where direct execution is necessary:

```bash
# Emergency override with justification
python .claude/workflow-enforcement/workflow-checker.py \
  --override \
  --justification "Critical production hotfix - no time for full workflow"
```

**Override Requirements:**
- Explicit justification required
- Automatically logged for review
- Must be approved in retrospective
- Should be exceptional, not routine

### 📊 Monitoring and Compliance

#### Check Compliance Status
```bash
python .claude/workflow-enforcement/workflow-checker.py --report
```

#### Validate Current Task
```bash
python .claude/workflow-enforcement/workflow-checker.py \
  --task "Your task description" \
  --files file1.py file2.py \
  --method orchestrator
```

#### Check Workflow Phases
```bash
python .claude/workflow-enforcement/workflow-checker.py --phases
```

### 🎯 Best Practices

1. **Always Start with Orchestrator** - For any code modification
2. **Trust the Process** - Each phase has important validation
3. **Don't Skip Steps** - All 11 phases serve a purpose
4. **Monitor Compliance** - Regularly check compliance reports
5. **Ask When Uncertain** - When in doubt, use orchestrator

### 💡 Benefits of Proper Workflow

- **Quality Assurance** - Comprehensive testing and validation
- **Risk Mitigation** - Isolated development in worktrees
- **Consistency** - Standardized approach across all changes
- **Traceability** - Full audit trail of all modifications
- **Team Coordination** - Clear process for collaboration

### 🔗 Related Resources

- **Orchestrator Documentation** - `.claude/orchestrator/README.md`
- **Workflow Manager Guide** - `.claude/agents/WorkflowMaster.md`
- **Troubleshooting Guide** - `.claude/instructions/troubleshooting.md`
- **Compliance Reports** - `.claude/workflow-enforcement/compliance_log.json`

### 📞 Getting Help

If you're unsure about workflow requirements:

1. Check this documentation
2. Run the workflow checker
3. Review compliance logs
4. Consult the orchestrator documentation
5. Ask for clarification rather than bypassing workflow

---

**Remember: The workflow exists to ensure quality, consistency, and reliability. Following it protects both your work and the entire codebase.**
