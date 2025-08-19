import os
import time
import subprocess
import json

#!/usr/bin/env python3
"""
Launch Claude terminals in VS Code for all git worktrees
"""

WORKTREES = [
    ("Main", "/Users/ryan/src/gadugi"),
    (
        "Memory-GitHub",
        "/Users/ryan/src/gadugi/.worktrees/memory-github-pr14-20250801-142454",
    ),
    (
        "PR-Backlog",
        "/Users/ryan/src/gadugi/.worktrees/pr-backlog-manager-implementation",
    ),
    (
        "PR25-Review",
        "/Users/ryan/src/gadugi/.worktrees/pr25-review-20250801-164649-4741",
    ),
    ("TeamCoach", "/Users/ryan/src/gadugi/.worktrees/teamcoach-implementation"),
    ("UV-Migration", "/Users/ryan/src/gadugi/.worktrees/uv-migration-20250802"),
]


def create_vscode_task_file():
    """Create a VS Code task file for launching terminals"""
    tasks = {"version": "2.0.0", "tasks": []}

    for name, path in WORKTREES:
        task = {
            "label": f"Claude: {name}",
            "type": "shell",
            "command": "claude",
            "options": {"cwd": path},
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "new",
                "group": f"claude-{name}",
            },
            "runOptions": {"runOn": "folderOpen"},
        }
        tasks["tasks"].append(task)

    os.makedirs(".vscode", exist_ok=True)
    with open(".vscode/claude-tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)

    print("Created .vscode/claude-tasks.json")
    print("You can now run these tasks from VS Code's command palette")


def launch_with_applescript():
    """Use AppleScript to control VS Code (macOS only)"""
    print("Launching Claude terminals in VS Code using AppleScript...")

    for i, (name, path) in enumerate(WORKTREES):
        script = f"""
        tell application "Visual Studio Code"
            activate
        end tell

        tell application "System Events"
            -- Open terminal
            keystroke "`" using {{command down}}
            delay 0.5

            -- Create new terminal if not first
            if {i} > 0 then
                keystroke "`" using {{command down, shift down}}
                delay 0.5
            end if

            -- Navigate to worktree
            keystroke "cd \\"{path}\\""
            keystroke return
            delay 0.3

            -- Start Claude
            keystroke "claude"
            keystroke return
        end tell
        """

        try:
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
            print(f"✓ Created terminal for {name}")
            time.sleep(1.5)  # Give VS Code time to process
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create terminal for {name}: {e}")


def main():
    print("Claude VS Code Terminal Launcher")
    print("================================\n")

    print("1. Creating VS Code task configuration...")
    create_vscode_task_file()

    print("\n2. Attempting to launch terminals automatically...")

    if os.uname().sysname == "Darwin":  # macOS
        launch_with_applescript()
    else:
        print("Automatic launch not supported on this OS.")
        print("Please use VS Code tasks: Cmd+Shift+P → 'Tasks: Run Task'")

    print("\nDone! Your Claude terminals should be starting in VS Code.")


if __name__ == "__main__":
    main()
