import * as vscode from 'vscode';
import { ErrorUtils } from '../utils/errorUtils';

/**
 * Service for handling Git setup guidance and user assistance
 */
export class GitSetupService {
  private static readonly DISMISS_KEY = 'gadugi.gitSetup.dismissed';
  private statusBarItem: vscode.StatusBarItem | undefined;

  constructor(private context: vscode.ExtensionContext) {
    this.initializeStatusBar();
  }

  /**
   * Initialize the git status bar item
   */
  private initializeStatusBar(): void {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      100
    );
    this.statusBarItem.command = 'gadugi.showGitStatus';
    this.context.subscriptions.push(this.statusBarItem);
    this.updateStatusBar();
  }

  /**
   * Update the status bar item based on current git state
   */
  public async updateStatusBar(): Promise<void> {
    if (!this.statusBarItem) return;

    try {
      const gitStatus = await this.getGitStatus();
      
      if (gitStatus.hasGit && gitStatus.hasRepository) {
        this.statusBarItem.text = '$(source-control) Git Ready';
        this.statusBarItem.tooltip = 'Git repository detected - Gadugi is ready';
        this.statusBarItem.backgroundColor = undefined;
      } else if (gitStatus.hasGit && !gitStatus.hasRepository) {
        this.statusBarItem.text = '$(warning) No Git Repo';
        this.statusBarItem.tooltip = 'Git installed but no repository found - Click to setup';
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
      } else {
        this.statusBarItem.text = '$(error) No Git';
        this.statusBarItem.tooltip = 'Git not installed - Click for setup help';
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
      }

      this.statusBarItem.show();
    } catch (error) {
      ErrorUtils.logError(
        error instanceof Error ? error : new Error(String(error)),
        ErrorUtils.createErrorContext('git-status-update')
      );
    }
  }

  /**
   * Get current git status
   */
  public async getGitStatus(): Promise<{
    hasGit: boolean;
    hasRepository: boolean;
    workspaceFolder: string | null;
  }> {
    let hasGit = false;
    let hasRepository = false;
    let workspaceFolder: string | null = null;

    // Check if git is installed
    try {
      const { execSync } = require('child_process');
      execSync('git --version', { stdio: 'ignore' });
      hasGit = true;
    } catch {
      // Git not available
    }

    // Check if we're in a git repository
    if (hasGit && vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
      workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath;
      try {
        const { execSync } = require('child_process');
        execSync('git rev-parse --git-dir', { cwd: workspaceFolder, stdio: 'ignore' });
        hasRepository = true;
      } catch {
        // Not a git repository
      }
    }

    return { hasGit, hasRepository, workspaceFolder };
  }

  /**
   * Show git setup guidance dialog
   */
  public async showGitSetupGuidance(): Promise<void> {
    try {
      // Check if user has dismissed this dialog
      const hasDismissed = this.context.workspaceState.get<boolean>(GitSetupService.DISMISS_KEY, false);
      if (hasDismissed) {
        return;
      }

      const gitStatus = await this.getGitStatus();
      
      if (gitStatus.hasGit && gitStatus.hasRepository) {
        // Everything is good, no need to show guidance
        return;
      }

      let message: string;
      let actions: string[];

      if (!gitStatus.hasGit) {
        message = `Gadugi requires Git to manage worktrees and development workflows.

Git is not installed or not available in your PATH. Please install Git first:
• Windows: Download from git-scm.com
• macOS: Install via Homebrew (brew install git) or Xcode Command Line Tools
• Linux: Use your package manager (e.g., apt install git)

After installing Git, restart VS Code and try again.`;

        actions = ['Install Git Guide', 'Dismiss', 'Don\'t Show Again'];
      } else if (!gitStatus.hasRepository) {
        message = `Gadugi needs a Git repository to manage worktrees and development workflows.

The current workspace is not a Git repository. You can:
• Clone an existing repository
• Initialize a new repository in this folder
• Open a different folder that contains a Git repository`;

        actions = ['Clone Repository', 'Initialize Repository', 'Open Folder', 'Dismiss', 'Don\'t Show Again'];
      } else {
        return;
      }

      const action = await vscode.window.showInformationMessage(
        message,
        { modal: false },
        ...actions
      );

      await this.handleGitSetupAction(action, gitStatus);

    } catch (error) {
      ErrorUtils.logError(
        error instanceof Error ? error : new Error(String(error)),
        ErrorUtils.createErrorContext('git-setup-guidance')
      );
    }
  }

  /**
   * Handle user action from git setup dialog
   */
  private async handleGitSetupAction(
    action: string | undefined,
    gitStatus: { hasGit: boolean; hasRepository: boolean; workspaceFolder: string | null }
  ): Promise<void> {
    if (!action) return;

    try {
      switch (action) {
        case 'Clone Repository':
          await vscode.commands.executeCommand('git.clone');
          break;

        case 'Initialize Repository':
          if (gitStatus.workspaceFolder) {
            const confirm = await vscode.window.showInformationMessage(
              `Initialize a Git repository in ${gitStatus.workspaceFolder}?`,
              { modal: true },
              'Yes',
              'No'
            );
            
            if (confirm === 'Yes') {
              await this.initializeRepository(gitStatus.workspaceFolder);
            }
          } else {
            await vscode.window.showErrorMessage('No workspace folder available to initialize');
          }
          break;

        case 'Open Folder':
          await vscode.commands.executeCommand('vscode.openFolder');
          break;

        case 'Install Git Guide':
          await vscode.env.openExternal(vscode.Uri.parse('https://git-scm.com/downloads'));
          break;

        case 'Don\'t Show Again':
          await this.context.workspaceState.update(GitSetupService.DISMISS_KEY, true);
          await vscode.window.showInformationMessage(
            'Git setup guidance disabled. You can re-enable it from the Command Palette: "Gadugi: Show Git Setup"'
          );
          break;

        case 'Dismiss':
          // Just close the dialog
          break;
      }

      // Update status bar after any action
      await this.updateStatusBar();

    } catch (error) {
      ErrorUtils.logError(
        error instanceof Error ? error : new Error(String(error)),
        ErrorUtils.createErrorContext('git-setup-action')
      );
    }
  }

  /**
   * Initialize a git repository in the specified folder
   */
  private async initializeRepository(folderPath: string): Promise<void> {
    try {
      const { execSync } = require('child_process');
      execSync('git init', { cwd: folderPath });
      
      await vscode.window.showInformationMessage(
        `Git repository initialized in ${folderPath}. You may want to create an initial commit.`
      );

      // Offer to create initial commit
      const createCommit = await vscode.window.showInformationMessage(
        'Would you like to create an initial commit?',
        'Yes',
        'No'
      );

      if (createCommit === 'Yes') {
        await this.createInitialCommit(folderPath);
      }

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('git-init'));
      await vscode.window.showErrorMessage(`Failed to initialize Git repository: ${err.message}`);
    }
  }

  /**
   * Create an initial commit
   */
  private async createInitialCommit(folderPath: string): Promise<void> {
    try {
      const { execSync } = require('child_process');
      
      // Create a basic .gitignore if it doesn't exist
      const fs = require('fs');
      const path = require('path');
      const gitignorePath = path.join(folderPath, '.gitignore');
      
      if (!fs.existsSync(gitignorePath)) {
        const gitignoreContent = `# VS Code
.vscode/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Node modules (if applicable)
node_modules/

# Build outputs
dist/
build/
out/
`;
        fs.writeFileSync(gitignorePath, gitignoreContent);
      }

      // Add and commit
      execSync('git add .', { cwd: folderPath });
      execSync('git commit -m "Initial commit"', { cwd: folderPath });
      
      await vscode.window.showInformationMessage('Initial commit created successfully!');

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('git-initial-commit'));
      await vscode.window.showErrorMessage(`Failed to create initial commit: ${err.message}`);
    }
  }

  /**
   * Show detailed git status information
   */
  public async showGitStatusDetails(): Promise<void> {
    try {
      const gitStatus = await this.getGitStatus();
      
      let message = 'Git Status for Gadugi Extension\n\n';
      
      if (gitStatus.hasGit) {
        message += '✅ Git is installed and available\n';
      } else {
        message += '❌ Git is not installed or not in PATH\n';
      }

      if (gitStatus.workspaceFolder) {
        message += `📁 Workspace: ${gitStatus.workspaceFolder}\n`;
        
        if (gitStatus.hasRepository) {
          message += '✅ Git repository detected\n';
          message += '\n🎉 All prerequisites met! Gadugi is ready to use.';
        } else {
          message += '❌ Not a Git repository\n';
          message += '\n⚠️ Gadugi requires a Git repository to function properly.';
        }
      } else {
        message += '❌ No workspace folder open\n';
        message += '\n⚠️ Please open a folder to use Gadugi.';
      }

      const actions: string[] = [];
      if (!gitStatus.hasGit) {
        actions.push('Install Git Guide');
      }
      if (!gitStatus.hasRepository && gitStatus.workspaceFolder) {
        actions.push('Setup Git Repository');
      }
      actions.push('OK');

      const action = await vscode.window.showInformationMessage(
        message,
        { modal: true },
        ...actions
      );

      if (action === 'Install Git Guide') {
        await vscode.env.openExternal(vscode.Uri.parse('https://git-scm.com/downloads'));
      } else if (action === 'Setup Git Repository') {
        await this.showGitSetupGuidance();
      }

    } catch (error) {
      ErrorUtils.logError(
        error instanceof Error ? error : new Error(String(error)),
        ErrorUtils.createErrorContext('git-status-details')
      );
    }
  }

  /**
   * Reset the dismiss preference
   */
  public async resetDismissPreference(): Promise<void> {
    await this.context.workspaceState.update(GitSetupService.DISMISS_KEY, false);
    await vscode.window.showInformationMessage('Git setup guidance has been re-enabled.');
  }

  /**
   * Dispose of resources
   */
  public dispose(): void {
    if (this.statusBarItem) {
      this.statusBarItem.dispose();
    }
  }
}