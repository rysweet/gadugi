#!/bin/bash

# Claude Code Worktree Session Manager
# This script helps manage Claude Code sessions across multiple worktrees

ACTION="${1:-status}"

case "$ACTION" in
    status)
        echo "Current Git Worktrees and Claude Sessions:"
        echo "=========================================="
        git worktree list | while read -r line; do
            worktree=$(echo "$line" | awk '{print $1}')
            branch=$(echo "$line" | sed 's/.*\[\(.*\)\].*/\1/')
            name=$(basename "$worktree")

            echo ""
            echo "Worktree: $name"
            echo "Path: $worktree"
            echo "Branch: $branch"

            # Check if Claude is running in this directory
            # Error suppression justified: lsof might not be available on all systems
            if lsof 2>/dev/null | grep -q "$worktree"; then
                echo "Claude Status: Possibly active"
            else
                echo "Claude Status: Not detected"
            fi
        done
        ;;

    launch)
        echo "VS Code Terminal Setup for Claude Worktrees"
        echo "==========================================="
        echo ""
        echo "Option 1: Manual Setup in VS Code"
        echo "---------------------------------"
        echo "1. Open VS Code integrated terminal (Ctrl/Cmd + \`)"
        echo "2. Create a new terminal for each worktree (+ icon or Ctrl/Cmd + Shift + \`)"
        echo "3. Right-click each terminal tab to rename it"
        echo "4. Run these commands in each terminal:"
        echo ""

        git worktree list | while read -r line; do
            worktree=$(echo "$line" | awk '{print $1}')
            name=$(basename "$worktree")
            branch=$(echo "$line" | sed 's/.*\[\(.*\)\].*/\1/')

            echo "Terminal: $name [$branch]"
            echo "  cd \"$worktree\" && claude"
            echo ""
        done

        echo "Option 2: VS Code Tasks (tasks.json)"
        echo "------------------------------------"
        echo "Creating VS Code tasks configuration..."

        # Create .vscode directory if it doesn't exist
        mkdir -p /Users/ryan/src/gadugi/.vscode

        # Generate tasks.json
        cat > /Users/ryan/src/gadugi/.vscode/claude-worktree-tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
EOF

        first=true
        git worktree list | while read -r line; do
            worktree=$(echo "$line" | awk '{print $1}')
            name=$(basename "$worktree")
            branch=$(echo "$line" | sed 's/.*\[\(.*\)\].*/\1/')

            if [ "$first" = false ]; then
                echo "," >> /Users/ryan/src/gadugi/.vscode/claude-worktree-tasks.json
            fi
            first=false

            cat >> /Users/ryan/src/gadugi/.vscode/claude-worktree-tasks.json << EOF
        {
            "label": "Claude: $name",
            "type": "shell",
            "command": "claude",
            "options": {
                "cwd": "$worktree"
            },
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": true,
                "panel": "new",
                "group": "$name"
            },
            "problemMatcher": []
        }
EOF
        done

        echo "" >> /Users/ryan/src/gadugi/.vscode/claude-worktree-tasks.json
        echo "    ]" >> /Users/ryan/src/gadugi/.vscode/claude-worktree-tasks.json
        echo "}" >> /Users/ryan/src/gadugi/.vscode/claude-worktree-tasks.json

        echo ""
        echo "VS Code tasks configuration created at: .vscode/claude-worktree-tasks.json"
        echo "To use: Cmd+Shift+P → 'Tasks: Run Task' → Select a Claude worktree task"
        echo ""
        echo "Option 3: Terminal Profile (settings.json)"
        echo "-----------------------------------------"
        echo "Add these terminal profiles to your VS Code settings to quickly launch terminals:"
        echo "(Copy the JSON below to your settings.json under 'terminal.integrated.profiles.osx')"
        ;;

    *)
        echo "Usage: $0 [status|launch]"
        echo "  status - Show worktree and Claude session status"
        echo "  launch - Launch Claude in all worktrees (macOS only)"
        ;;
esac
