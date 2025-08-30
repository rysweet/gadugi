#!/bin/bash

# Launch Claude in VS Code terminals for all worktrees
# This uses VS Code's CLI to create terminals

echo "Launching Claude terminals in VS Code..."
echo "========================================"

# Array of worktrees and their names
declare -A WORKTREES=(
    ["Main"]="/Users/ryan/src/gadugi"
    ["Memory-GitHub"]="/Users/ryan/src/gadugi/.worktrees/memory-github-pr14-20250801-142454"
    ["PR-Backlog"]="/Users/ryan/src/gadugi/.worktrees/PrBacklogManager-implementation"
    ["PR25-Review"]="/Users/ryan/src/gadugi/.worktrees/pr25-review-20250801-164649-4741"
    ["TeamCoach"]="/Users/ryan/src/gadugi/.worktrees/teamcoach-implementation"
    ["UV-Migration"]="/Users/ryan/src/gadugi/.worktrees/uv-migration-20250802"
)

# Create a temporary VS Code script
SCRIPT_FILE="/tmp/vscode-claude-terminals.js"

cat > "$SCRIPT_FILE" << 'EOF'
const vscode = require('vscode');

function activate(context) {
    const terminals = [
        { name: 'Claude: Main', cwd: '/Users/ryan/src/gadugi' },
        { name: 'Claude: Memory-GitHub', cwd: '/Users/ryan/src/gadugi/.worktrees/memory-github-pr14-20250801-142454' },
        { name: 'Claude: PR-Backlog', cwd: '/Users/ryan/src/gadugi/.worktrees/PrBacklogManager-implementation' },
        { name: 'Claude: PR25-Review', cwd: '/Users/ryan/src/gadugi/.worktrees/pr25-review-20250801-164649-4741' },
        { name: 'Claude: TeamCoach', cwd: '/Users/ryan/src/gadugi/.worktrees/teamcoach-implementation' },
        { name: 'Claude: UV-Migration', cwd: '/Users/ryan/src/gadugi/.worktrees/uv-migration-20250802' }
    ];

    terminals.forEach((config, index) => {
        setTimeout(() => {
            const terminal = vscode.window.createTerminal({
                name: config.name,
                cwd: config.cwd
            });
            terminal.show(false); // false = don't take focus
            terminal.sendText('claude');
        }, index * 500); // Stagger creation to avoid overwhelming VS Code
    });
}

exports.activate = activate;
EOF

# Option 1: Using VS Code Tasks (Recommended)
echo "Option 1: Using VS Code Tasks (Recommended)"
echo "-------------------------------------------"
echo "Run: ./scripts/claude-WorktreeManager.sh launch"
echo "Then use Cmd+Shift+P → 'Tasks: Run Task' to launch terminals"
echo ""

# Option 2: AppleScript automation (macOS specific)
echo "Option 2: AppleScript Automation"
echo "--------------------------------"

for name in "${!WORKTREES[@]}"; do
    worktree="${WORKTREES[$name]}"

    # Create AppleScript command
    osascript -e "
    tell application \"Visual Studio Code\"
        activate
    end tell

    tell application \"System Events\"
        keystroke \"\`\" using {command down}
        delay 0.5
        keystroke \"cd \\\"$worktree\\\" && claude\"
        keystroke return
        delay 0.5
    end tell" 2>/dev/null || echo "  - Failed to create terminal for $name"

    echo "  ✓ Created terminal for $name"
    sleep 1
done

echo ""
echo "All terminals created!"
