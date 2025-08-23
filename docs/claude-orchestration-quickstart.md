# CLAUDE.md Orchestration Quick Start Guide

## Introduction

This guide gets you started quickly with the new CLAUDE.md-based orchestration system.

## Core Concept

**Everything you need is in CLAUDE.md.** No separate orchestrator agents needed.

## Quick Start Examples

### Example 1: Single Task Execution

**Task:** Fix a bug in the parser module

```bash
# Step 1: Create issue
gh issue create --title "fix: parser bug with empty input" \
  --body "Parser crashes when given empty input string"

# Step 2: Create worktree
ISSUE=306
git worktree add .worktrees/issue-$ISSUE -b feature/issue-$ISSUE-parser-fix

# Step 3: Navigate to worktree
cd .worktrees/issue-$ISSUE

# Step 4: Make changes
# [Edit src/parser.py to fix the bug]

# Step 5: Test
uv run pytest tests/test_parser.py -v
uv run ruff check .
uv run pre-commit run --all-files

# Step 6: Commit
git add -A
git commit -m "fix: handle empty input in parser

- Added validation for empty strings
- Added test case for empty input
- Fixes #306"

# Step 7: Push and create PR
git push -u origin feature/issue-$ISSUE-parser-fix
gh pr create --base main --title "fix: parser bug with empty input (#$ISSUE)"

# Step 8: Clean up after merge
cd ../../
git worktree remove .worktrees/issue-$ISSUE
```

### Example 2: Parallel Task Execution

**Task:** Fix three independent bugs

```python
#!/usr/bin/env python3
"""Execute three bug fixes in parallel"""

import subprocess
import threading

def fix_bug(issue_num, description):
    """Fix a single bug in its own worktree"""
    
    # Create worktree
    worktree = f".worktrees/issue-{issue_num}"
    branch = f"feature/issue-{issue_num}-fix"
    
    subprocess.run([
        "git", "worktree", "add", worktree, "-b", branch
    ])
    
    # Make fixes in worktree
    # ... implementation ...
    
    # Test
    subprocess.run(["uv", "run", "pytest"], cwd=worktree)
    
    # Commit and push
    subprocess.run(["git", "add", "-A"], cwd=worktree)
    subprocess.run(["git", "commit", "-m", f"fix: {description}"], cwd=worktree)
    subprocess.run(["git", "push", "-u", "origin", branch], cwd=worktree)
    
    # Create PR
    subprocess.run([
        "gh", "pr", "create", 
        "--base", "main",
        "--title", f"fix: {description} (#{issue_num})"
    ])

# Execute fixes in parallel
bugs = [
    (307, "null pointer in validator"),
    (308, "memory leak in cache"),
    (309, "race condition in worker")
]

threads = []
for issue, desc in bugs:
    t = threading.Thread(target=fix_bug, args=(issue, desc))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

### Example 3: Using Executor Agents

When you need specific operations, use simplified executors:

```bash
# Worktree operations
/agent:worktree-executor
Create worktree for issue 310, feature branch

# GitHub operations
/agent:github-executor
Create issue titled "Add user authentication"

# Test operations
/agent:test-executor
Run full test suite with coverage

# Code operations
/agent:code-executor
Create new module src/auth.py with Auth class
```

## The 11-Phase Workflow

Every change follows these phases:

1. **Initial Setup** - Understand requirements
2. **Issue Creation** - Create GitHub issue
3. **Branch/Worktree** - Isolated environment
4. **Research** - Analyze codebase
5. **Implementation** - Write code
6. **Testing** - Run all tests (MANDATORY)
7. **Documentation** - Update docs
8. **PR Creation** - Create pull request
9. **Review** - Code review process
10. **Response** - Address feedback
11. **Merge/Cleanup** - Complete and clean

## Key Commands Reference

### Git Worktree
```bash
git worktree add .worktrees/name -b branch    # Create
git worktree list                             # List all
git worktree remove .worktrees/name          # Remove
```

### GitHub CLI
```bash
gh issue create --title "Title" --body "Body"        # Create issue
gh pr create --base main --title "Title"            # Create PR
gh pr merge NUMBER --squash                         # Merge PR
```

### Testing (UV Projects)
```bash
uv sync --all-extras          # Setup environment
uv run pytest tests/          # Run tests
uv run ruff check .          # Lint code
uv run ruff format .         # Format code
uv run pyright              # Type check
uv run pre-commit run --all-files  # Pre-commit hooks
```

## Tips for Success

1. **Always follow the 11 phases** - Don't skip steps
2. **Test before PR** - All tests must pass
3. **Use worktrees** - Keep main branch clean
4. **Document changes** - Update relevant docs
5. **Clean up** - Remove worktrees after merge

## Common Pitfalls to Avoid

❌ **Don't:** Try to find OrchestratorAgent (deprecated)
✅ **Do:** Follow CLAUDE.md directly

❌ **Don't:** Skip testing phase
✅ **Do:** Run all tests before creating PR

❌ **Don't:** Work directly on main branch
✅ **Do:** Always use worktrees or feature branches

❌ **Don't:** Create complex agent chains
✅ **Do:** Use simple executor agents when needed

## Getting Started Checklist

- [ ] Read CLAUDE.md completely
- [ ] Understand the 11-phase workflow
- [ ] Try a simple single-task example
- [ ] Try a parallel execution example
- [ ] Use each executor agent once
- [ ] Complete one full workflow cycle

## Need Help?

- **First:** Check CLAUDE.md for detailed instructions
- **Second:** Review this quick start guide
- **Third:** See migration guide for specific scenarios
- **Last:** Create an issue for clarification

Remember: Simplicity is the goal. When in doubt, follow CLAUDE.md.
