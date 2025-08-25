# Worktree Cleanup Documentation

## Overview

The Worktree Cleanup functionality provides automated and manual cleanup of Git worktrees to maintain repository hygiene and prevent disk space issues. This feature is integrated into the WorkflowManager as Phase 14 and includes a standalone cleanup script.

## Components

### 1. Cleanup Script
**Location**: `.claude/scripts/cleanup-worktrees.sh`

A comprehensive Bash script that safely removes Git worktrees with the following features:
- Automatic detection and preservation of the current worktree
- Dry-run mode for preview
- Force mode for removing worktrees with uncommitted changes
- Automatic pruning of stale references
- Colored output for better visibility
- Error handling and recovery

### 2. WorkflowManager Integration
**Location**: `.claude/agents/workflow-manager.md`

Phase 14 has been added to the WorkflowManager to automatically clean up worktrees at the end of each workflow:
- Runs automatically after Phase 13 (Team Coach Reflection)
- Non-blocking - failures don't prevent workflow completion
- Provides visibility into worktree status

## Usage

### Manual Cleanup

#### Basic Usage
```bash
# Remove all worktrees except the current one
./.claude/scripts/cleanup-worktrees.sh
```

#### Dry Run Mode
```bash
# Preview what would be removed without making changes
./.claude/scripts/cleanup-worktrees.sh --dry-run
```

#### Force Mode
```bash
# Remove worktrees even if they have uncommitted changes
./.claude/scripts/cleanup-worktrees.sh --force
```

#### Help
```bash
# Show usage information
./.claude/scripts/cleanup-worktrees.sh --help
```

### Automatic Cleanup

The cleanup process runs automatically as Phase 14 of the WorkflowManager workflow:

1. Triggered after Phase 13 (Team Coach Reflection) completes
2. Runs the cleanup script in safe mode
3. Reports results but doesn't block workflow completion
4. Updates workflow state to mark completion

## Safety Features

### Current Worktree Protection
The script automatically detects and skips the current worktree to prevent self-removal.

### Uncommitted Changes Detection
By default, worktrees with uncommitted changes are preserved unless `--force` is used.

### Dry Run Mode
Always preview changes before actual removal using `--dry-run`.

### Error Recovery
The script continues processing even if individual worktree removals fail.

### Automatic Pruning
After removing worktrees, `git worktree prune` is automatically run to clean up stale references.

## Output

The script provides colored output for better visibility:
- **Blue [INFO]**: General information messages
- **Green [SUCCESS]**: Successful operations
- **Yellow [WARNING]**: Non-critical issues or skipped operations
- **Red [ERROR]**: Failed operations

### Example Output
```
[INFO] Starting worktree cleanup process...
[INFO] Current worktree: /path/to/current/worktree
[INFO] Scanning for worktrees to clean up...
[INFO] Skipping current worktree: task-current
[SUCCESS] Removed worktree: task-old-1
[WARNING] Worktree has uncommitted changes: task-old-2 (use --force to remove anyway)
[SUCCESS] Removed worktree: task-old-3
[INFO] Running git worktree prune...
[SUCCESS] Pruned stale worktree references

[INFO] Cleanup Summary:
[INFO]   Worktrees removed: 2
[INFO]   Worktrees skipped: 1
[WARNING]   Worktrees failed: 1

[INFO] Current worktree status:
/path/to/main/repo     abc123 [main]
/path/to/current/worktree  def456 [feature/current]
/path/to/task-old-2    ghi789 [feature/old-2]
```

## Integration with Workflow Phases

### Phase 14 Execution Flow

1. **Automatic Trigger**: Executed after Phase 13 completion
2. **Script Execution**: Runs cleanup script with safe defaults
3. **Error Handling**: Failures are logged but don't block workflow
4. **State Update**: Marks Phase 14 as complete
5. **Final Report**: Shows remaining worktrees

### Configuration

The Phase 14 integration includes:
- **Priority**: Low (optional maintenance task)
- **Auto-invoke**: True (runs automatically)
- **Enforcement Level**: OPTIONAL (not required for workflow success)

## Troubleshooting

### Common Issues

#### Script Not Found
```bash
# Ensure the script exists and is executable
ls -la .claude/scripts/cleanup-worktrees.sh
chmod +x .claude/scripts/cleanup-worktrees.sh
```

#### Permission Denied
```bash
# Make the script executable
chmod +x .claude/scripts/cleanup-worktrees.sh
```

#### Worktree Locked
```bash
# Unlock and force remove
git worktree unlock /path/to/worktree
git worktree remove --force /path/to/worktree
```

#### Stale References
```bash
# Run manual prune
git worktree prune
```

## Best Practices

1. **Regular Cleanup**: Run cleanup after completing major tasks
2. **Check Before Force**: Always run with `--dry-run` before using `--force`
3. **Preserve Active Work**: Don't remove worktrees with uncommitted changes unless necessary
4. **Monitor Disk Space**: Regular cleanup prevents disk space issues
5. **Automated Workflow**: Let Phase 14 handle routine cleanup automatically

## Maintenance

### Updating the Script
The cleanup script is located at `.claude/scripts/cleanup-worktrees.sh` and can be modified to:
- Add additional safety checks
- Customize cleanup criteria
- Modify output formatting
- Add new command-line options

### Updating WorkflowManager Integration
Phase 14 configuration in `.claude/agents/workflow-manager.md` can be modified to:
- Change execution priority
- Modify error handling behavior
- Add additional validation steps
- Customize completion criteria

## Related Documentation

- [WorkflowManager Documentation](./../agents/workflow-manager.md)
- [Worktree Manager Agent](./../agents/worktree-manager.md)
- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)
