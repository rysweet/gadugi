
## 🚀 New: CLAUDE.md-Based Orchestration

Gadugi now uses a simplified orchestration model with all workflow logic integrated directly into CLAUDE.md. This eliminates complex agent delegation chains and provides a more reliable, understandable development workflow.

### Key Features

- **Integrated Orchestration**: All workflow phases defined in CLAUDE.md
- **11-Phase Workflow**: Mandatory structured approach for all changes
- **Parallel Execution**: Built-in support for independent task execution
- **Simplified Executors**: Single-purpose agents for specific operations

### Quick Start

1. **Read CLAUDE.md** for complete workflow instructions
2. **Follow the 11 phases** for any code change
3. **Use executor agents** when you need specific operations:
   - `WorktreeExecutor`: Git worktree operations
   - `GitHubExecutor`: GitHub issue/PR operations
   - `TestExecutor`: Test execution
   - `CodeExecutor`: Code writing/editing

### Example Workflow

```bash
# 1. Create issue
gh issue create --title "feat: add new feature"

# 2. Create worktree
git worktree add .worktrees/issue-123 -b feature/issue-123

# 3. Implement changes
cd .worktrees/issue-123
# ... make changes ...

# 4. Test
uv run pytest tests/
uv run ruff check .

# 5. Create PR
git push -u origin feature/issue-123
gh pr create --base main

# 6. Clean up after merge
git worktree remove .worktrees/issue-123
```

For detailed instructions, see:
- [CLAUDE.md](./CLAUDE.md) - Complete orchestration instructions
- [Quick Start Guide](./docs/claude-orchestration-quickstart.md)
- [Migration Guide](./docs/migration-to-claude-orchestration.md)

