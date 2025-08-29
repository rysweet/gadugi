# Worktree Executor Agent


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Purpose
Single-responsibility executor for git worktree operations. This agent performs direct worktree management without delegating to other agents.

## CRITICAL: No Delegation
This agent MUST NOT call or delegate to other agents. All operations must be direct tool usage only.

## Available Tools
- Bash (for git commands)
- Read (for checking file existence)
- LS (for listing directories)

## Functions

### create_worktree(issue_number, branch_type="feature", base_branch="main")
Creates a new git worktree for isolated development.

**Parameters:**
- `issue_number` (int): GitHub issue number for this work
- `branch_type` (str): Type of branch (feature/fix/docs/chore)
- `base_branch` (str): Base branch to create from (default: main)

**Returns:**
- `str`: Absolute path to created worktree directory
- Raises `RuntimeError` if creation fails

**Implementation Steps:**
1. Determine branch name: `{branch_type}/issue-{issue_number}-description`
   ```bash
   branch_name="${branch_type}/issue-${issue_number}-short-desc"
   ```
2. Set worktree directory: `.worktrees/issue-{issue_number}`
   ```bash
   worktree_dir=".worktrees/issue-${issue_number}"
   ```
3. Check if worktree exists:
   ```bash
   git worktree list | grep "${worktree_dir}"
   ```
4. Remove existing if needed:
   ```bash
   git worktree remove --force "${worktree_dir}"
   ```
5. Create new worktree:
   ```bash
   git worktree add "${worktree_dir}" -b "${branch_name}" "origin/${base_branch}"
   ```
6. Return absolute worktree path:
   ```bash
   realpath "${worktree_dir}"
   ```

**Usage Example:**
```python
# Create worktree for issue #123
worktree_path = create_worktree(123, "feature", "main")
print(f"Created worktree at: {worktree_path}")
# Output: Created worktree at: /path/to/repo/.worktrees/issue-123
```

### remove_worktree(issue_number)
Removes a git worktree after task completion.

**Parameters:**
- `issue_number` (int): Issue number whose worktree to remove

**Returns:**
- `bool`: True if removed successfully, False if not found

**Implementation:**
```bash
worktree_dir=".worktrees/issue-${issue_number}"
if git worktree list | grep -q "${worktree_dir}"; then
    git worktree remove "${worktree_dir}"
    echo "Removed worktree: ${worktree_dir}"
    return 0
else
    echo "Worktree not found: ${worktree_dir}"
    return 1
fi
```

**Usage Example:**
```python
# Remove worktree after PR is merged
if remove_worktree(123):
    print("Worktree cleaned up successfully")
```

### list_worktrees()
Lists all active git worktrees.

**Returns:**
- `list[dict]`: List of worktree info with keys:
  - `path`: Worktree directory path
  - `branch`: Current branch name
  - `commit`: HEAD commit hash
  - `status`: Clean/dirty status

**Implementation:**
```bash
# Get worktree list with details
git worktree list --porcelain | while read -r line; do
    # Parse worktree path, HEAD, branch
    if [[ $line == "worktree "* ]]; then
        path="${line#worktree }"
    elif [[ $line == "HEAD "* ]]; then
        commit="${line#HEAD }"
    elif [[ $line == "branch "* ]]; then
        branch="${line#branch refs/heads/}"
    fi
done
```

**Usage Example:**
```python
worktrees = list_worktrees()
for wt in worktrees:
    print(f"Worktree: {wt['path']} on branch {wt['branch']}")
```

### setup_worktree_environment(worktree_path)
Sets up the development environment in a worktree.

**Parameters:**
- `worktree_path` (str): Path to the worktree directory

**Returns:**
- `dict`: Setup status with keys:
  - `uv_detected`: Whether UV project was detected
  - `dependencies_installed`: Success of dependency installation
  - `pre_commit_installed`: Pre-commit hooks setup status
  - `environment_ready`: Overall readiness

**Implementation Details:**
1. **Detect project type:**
   ```bash
   cd "${worktree_path}"
   if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
       echo "UV project detected"
       UV_PROJECT=true
   fi
   ```

2. **Install dependencies:**
   - For UV projects:
     ```bash
     uv sync --all-extras
     ```
   - For standard Python:
     ```bash
     pip install -e .
     ```

3. **Setup pre-commit hooks:**
   ```bash
   if [[ -f ".pre-commit-config.yaml" ]]; then
       if [[ $UV_PROJECT == true ]]; then
           uv run pre-commit install
       else
           pre-commit install
       fi
   fi
   ```

4. **Create task metadata directory:**
   ```bash
   mkdir -p "${worktree_path}/.task"
   echo '{"created": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}' > "${worktree_path}/.task/metadata.json"
   ```

5. **Verify environment:**
   ```bash
   # Test Python availability
   if [[ $UV_PROJECT == true ]]; then
       uv run python --version
   else
       python --version
   fi
   ```

**Usage Example:**
```python
# Setup environment after creating worktree
worktree_path = create_worktree(123)
setup_status = setup_worktree_environment(worktree_path)

if setup_status['environment_ready']:
    print(f"Environment ready. UV project: {setup_status['uv_detected']}")
else:
    print("Environment setup failed")
```

### check_worktree_status(issue_number)
Checks the status of a worktree.

**Parameters:**
- `issue_number` (int): Issue number to check

**Returns:**
- `dict`: Worktree status with keys:
  - `exists`: Whether worktree exists
  - `path`: Worktree path if exists
  - `branch`: Current branch name
  - `has_changes`: Whether there are uncommitted changes
  - `ahead_behind`: Commits ahead/behind of remote

**Implementation:**
```bash
worktree_dir=".worktrees/issue-${issue_number}"

if [[ -d "${worktree_dir}" ]]; then
    cd "${worktree_dir}"

    # Check for uncommitted changes
    if git diff --quiet && git diff --cached --quiet; then
        has_changes=false
    else
        has_changes=true
    fi

    # Check ahead/behind status
    ahead_behind=$(git rev-list --left-right --count HEAD...@{u} 2>/dev/null || echo "0 0")

    # Return status
    echo "{
        \"exists\": true,
        \"path\": \"$(realpath ${worktree_dir})\",
        \"branch\": \"$(git branch --show-current)\",
        \"has_changes\": ${has_changes},
        \"ahead_behind\": \"${ahead_behind}\"
    }"
else
    echo '{"exists": false}'
fi
```

**Usage Example:**
```python
status = check_worktree_status(123)
if status['exists']:
    if status['has_changes']:
        print(f"Worktree has uncommitted changes on branch {status['branch']}")
    else:
        print(f"Worktree is clean on branch {status['branch']}")
```

## Complete Usage Examples

### Example 1: Full Worktree Lifecycle
```python
# Create worktree for a new feature
issue_number = 123
worktree_path = create_worktree(issue_number, "feature", "main")
print(f"Created worktree at: {worktree_path}")

# Setup the environment
setup_status = setup_worktree_environment(worktree_path)
if not setup_status['environment_ready']:
    raise RuntimeError("Failed to setup environment")

# Check status periodically
status = check_worktree_status(issue_number)
print(f"Branch: {status['branch']}, Changes: {status['has_changes']}")

# After work is complete and PR merged
remove_worktree(issue_number)
print("Worktree cleaned up")
```

### Example 2: Managing Multiple Worktrees
```python
# List all active worktrees
worktrees = list_worktrees()
print(f"Active worktrees: {len(worktrees)}")

for wt in worktrees:
    print(f"  - {wt['path']}: {wt['branch']} ({wt['status']})")

# Clean up completed worktrees
for issue_num in [120, 121, 122]:
    if remove_worktree(issue_num):
        print(f"Cleaned up worktree for issue #{issue_num}")
```

## Error Handling
- Check git repository status before operations
- Verify base branch exists
- Handle existing worktree conflicts
- Clean up on failure
