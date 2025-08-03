#!/bin/bash

# Script to restart Claude Code in each worktree with clear identification

WORKTREES=(
    "/Users/ryan/src/gadugi"
    "/Users/ryan/src/gadugi/.worktrees/memory-github-pr14-20250801-142454"
    "/Users/ryan/src/gadugi/.worktrees/pr-backlog-manager-implementation"
    "/Users/ryan/src/gadugi/.worktrees/pr25-review-20250801-164649-4741"
    "/Users/ryan/src/gadugi/.worktrees/teamcoach-implementation"
    "/Users/ryan/src/gadugi/.worktrees/uv-migration-20250802"
)

echo "Claude Code Worktree Restart Helper"
echo "==================================="
echo ""
echo "Open 6 separate terminal windows/tabs and run the following commands:"
echo ""

for i in "${!WORKTREES[@]}"; do
    worktree="${WORKTREES[$i]}"
    name=$(basename "$worktree")
    branch=$(cd "$worktree" && git branch --show-current 2>/dev/null || echo "unknown")
    
    echo "Terminal $((i+1)) - $name [$branch]:"
    echo "  cd \"$worktree\" && claude"
    echo ""
done

echo "TIP: You can rename your terminal tabs to match the worktree names for easy identification."
echo ""
echo "Alternative: Use tmux or screen sessions with named windows:"
echo "  tmux new-session -s gadugi-claude"
echo "  Then create windows with Ctrl-b c and rename with Ctrl-b ,"