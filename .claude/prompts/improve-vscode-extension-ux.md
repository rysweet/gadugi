# Improve VS Code Extension UX for Git Repository Requirement

## Context
The Gadugi VS Code extension currently fails silently when opened in a non-git repository workspace. Users see no UI panels and only a warning in the logs that they likely won't notice. This creates a poor user experience.

## Current Behavior
- Extension activates but shows warning only in output logs
- No UI panels appear because of `workspaceHasGitRepo` condition
- Users are confused about why the extension appears to do nothing

## Requirements
1. **User-Friendly Dialog**: When extension activates without a git repository, show an informative dialog explaining:
   - Why the extension needs a git repository
   - What features require git
   - How to fix the issue

2. **Action Buttons**: The dialog should have:
   - "Clone Repository" - Executes `git.clone` command to open VS Code's clone dialog
   - "Initialize Repository" - Executes `git.init` command in current workspace
   - "Open Folder" - Opens folder picker to select an existing git repository
   - "Dismiss" - Closes dialog

3. **Improved Activation**: 
   - Show limited UI even without git (e.g., setup instructions view)
   - Add status bar item showing git repository status
   - Provide clear visual feedback about missing prerequisites

4. **Better Error Handling**:
   - Check for git installation separately from repository check
   - Provide specific guidance for each missing prerequisite
   - Remember user's dismiss choice (don't spam on every activation)

## Implementation Notes
- Use `vscode.window.showInformationMessage` with action buttons
- Store dismiss preference in workspace state
- Consider creating a "Getting Started" webview for non-git workspaces
- Ensure extension provides value even without full git functionality

## Success Criteria
- Users immediately understand why extension isn't showing panels
- One-click actions to resolve the issue
- No confusion about extension requirements
- Graceful degradation when prerequisites aren't met