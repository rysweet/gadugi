import * as vscode from 'vscode';
import { GitService } from '../services/gitService';
import { TerminalService } from '../services/terminalService';
import { ClaudeService } from '../services/claudeService';
import { BloomCommandResult } from '../types';
import { ErrorUtils } from '../utils/errorUtils';
// PathUtils imported for potential future use
// import { PathUtils } from '../utils/pathUtils';

/**
 * Implementation of the Bloom command for the Gadugi VS Code extension
 */
export class BloomCommand {
  private gitService: GitService;
  private terminalService: TerminalService;
  private claudeService: ClaudeService;

  constructor() {
    this.gitService = new GitService();
    this.terminalService = new TerminalService();
    this.claudeService = new ClaudeService();
  }

  /**
   * Execute the Bloom command
   */
  async execute(): Promise<BloomCommandResult> {
    const result: BloomCommandResult = {
      success: false,
      terminalsCreated: 0,
      claudeInstancesStarted: 0,
      errors: []
    };

    try {
      // Show progress indicator
      return await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Bloom: Setting up Claude terminals for all worktrees',
          cancellable: false
        },
        async (progress) => {
          return await this.executeWithProgress(progress, result);
        }
      );
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('bloom-command-execution'));
      result.errors.push(err.message);
      return result;
    }
  }

  /**
   * Execute the command with progress reporting
   */
  private async executeWithProgress(
    progress: vscode.Progress<{ message?: string; increment?: number }>,
    result: BloomCommandResult
  ): Promise<BloomCommandResult> {
    try {
      // Step 1: Validate prerequisites
      progress.report({ message: 'Validating prerequisites...', increment: 10 });
      const validationResult = await this.validatePrerequisites();
      if (!validationResult.valid) {
        result.errors.push(...validationResult.errors);
        return result;
      }

      // Step 2: Discover worktrees
      progress.report({ message: 'Discovering git worktrees...', increment: 20 });
      const worktrees = await this.gitService.getWorktrees();

      if (worktrees.length === 0) {
        result.errors.push('No git worktrees found in the current workspace');
        return result;
      }

      ErrorUtils.logInfo(`Found ${worktrees.length} worktrees`, 'bloom-command');

      // Step 3: Get Claude command
      const claudeCommand = this.claudeService.getClaudeCommand();

      // Step 4: Create terminals for each worktree
      progress.report({ message: `Creating terminals for ${worktrees.length} worktrees...`, increment: 30 });

      let terminalsCreated = 0;
      let claudeInstancesStarted = 0;
      const errors: string[] = [];

      for (let i = 0; i < worktrees.length; i++) {
        const worktree = worktrees[i];
        const worktreeName = this.gitService.getWorktreeDisplayName(worktree);

        progress.report({
          message: `Setting up terminal for ${worktreeName} (${i + 1}/${worktrees.length})...`,
          increment: 40 / worktrees.length
        });

        try {
          // Create terminal for this worktree
          const terminal = await this.terminalService.createWorktreeTerminal(
            worktree.path,
            worktreeName,
            claudeCommand
          );

          if (terminal) {
            terminalsCreated++;
            claudeInstancesStarted++; // Assuming Claude starts successfully in the terminal
            ErrorUtils.logInfo(`Created terminal for worktree: ${worktreeName}`, 'bloom-command');
          } else {
            errors.push(`Failed to create terminal for worktree: ${worktreeName}`);
          }

          // Small delay between terminal creations
          await new Promise(resolve => setTimeout(resolve, 250));

        } catch (error) {
          const err = error instanceof Error ? error : new Error(String(error));
          const errorMessage = `Error setting up worktree ${worktreeName}: ${err.message}`;
          errors.push(errorMessage);
          ErrorUtils.logError(err, ErrorUtils.createErrorContext('bloom-worktree-setup', { worktree, worktreeName }));
        }
      }

      // Step 5: Final reporting
      progress.report({ message: 'Finalizing setup...', increment: 20 });

      result.terminalsCreated = terminalsCreated;
      result.claudeInstancesStarted = claudeInstancesStarted;
      result.errors = errors;
      result.success = terminalsCreated > 0;

      // Show completion message
      await this.showCompletionMessage(result);

      return result;

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('bloom-command-progress'));
      result.errors.push(err.message);
      return result;
    }
  }

  /**
   * Validate prerequisites for the Bloom command
   */
  private async validatePrerequisites(): Promise<{ valid: boolean; errors: string[] }> {
    const errors: string[] = [];

    try {
      // Check if workspace is open
      if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
        errors.push('No workspace folder is open');
      }

      // Check if it's a git repository
      const isGitRepo = await this.gitService.isGitRepository();
      if (!isGitRepo) {
        errors.push('Current workspace is not a git repository');
      }

      // Check if Claude is installed
      const claudeInstallation = await this.claudeService.isClaudeInstalled();
      if (!claudeInstallation.installed) {
        errors.push(`Claude Code is not installed: ${claudeInstallation.error || 'Unknown error'}`);
      }

      // Check terminal support
      const terminalSupport = await this.terminalService.validateTerminalSupport();
      if (!terminalSupport.supported) {
        errors.push(...terminalSupport.issues);
      }

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      errors.push(`Validation error: ${err.message}`);
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Show completion message to the user
   */
  private async showCompletionMessage(result: BloomCommandResult): Promise<void> {
    if (result.success) {
      const message = `Bloom completed successfully! Created ${result.terminalsCreated} terminals and started ${result.claudeInstancesStarted} Claude instances.`;

      if (result.errors.length > 0) {
        const action = await ErrorUtils.showWarningMessage(
          `${message} However, ${result.errors.length} issues were encountered.`,
          'Show Details',
          'Dismiss'
        );

        if (action === 'Show Details') {
          ErrorUtils.showOutput();
        }
      } else {
        await ErrorUtils.showInfoMessage(message);
      }

      ErrorUtils.logInfo(`Bloom command completed: ${result.terminalsCreated} terminals, ${result.claudeInstancesStarted} Claude instances`, 'bloom-command');
    } else {
      const message = `Bloom command failed. ${result.errors.length} error(s) occurred.`;
      const action = await ErrorUtils.showErrorMessage(message, 'Show Details', 'Dismiss');

      if (action === 'Show Details') {
        ErrorUtils.showOutput();
      }

      ErrorUtils.logError(new Error('Bloom command failed'), ErrorUtils.createErrorContext('bloom-command-completion', result));
    }
  }

  /**
   * Get a preview of what the Bloom command will do
   */
  async getExecutionPreview(): Promise<{
    worktreeCount: number;
    worktreeNames: string[];
    claudeCommand: string;
    issues: string[];
  }> {
    const preview = {
      worktreeCount: 0,
      worktreeNames: [] as string[],
      claudeCommand: '',
      issues: [] as string[]
    };

    try {
      // Get worktrees
      const worktrees = await this.gitService.getWorktrees();
      preview.worktreeCount = worktrees.length;
      preview.worktreeNames = worktrees.map(w => this.gitService.getWorktreeDisplayName(w));

      // Get Claude command
      preview.claudeCommand = this.claudeService.getClaudeCommand();

      // Check for potential issues
      const validation = await this.validatePrerequisites();
      preview.issues = validation.errors;

      if (worktrees.length === 0) {
        preview.issues.push('No worktrees found - only main repository');
      }

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      preview.issues.push(`Preview error: ${err.message}`);
    }

    return preview;
  }

  /**
   * Show execution preview to user
   */
  async showExecutionPreview(): Promise<boolean> {
    const preview = await this.getExecutionPreview();

    if (preview.issues.length > 0) {
      const message = `Cannot execute Bloom command due to issues:\n${preview.issues.join('\n')}`;
      await ErrorUtils.showErrorMessage(message);
      return false;
    }

    const message = `Bloom will create ${preview.worktreeCount} terminals for these worktrees:\n${preview.worktreeNames.join(', ')}\n\nCommand: ${preview.claudeCommand}`;
    const action = await vscode.window.showInformationMessage(message, 'Execute', 'Cancel');

    return action === 'Execute';
  }

  /**
   * Register the Bloom command with VS Code
   */
  static register(_context: vscode.ExtensionContext): vscode.Disposable {
    const bloomCommand = new BloomCommand();

    return vscode.commands.registerCommand('gadugi.bloom', async () => {
      try {
        ErrorUtils.logInfo('Bloom command invoked', 'bloom-command');
        await bloomCommand.execute();
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        ErrorUtils.logError(err, ErrorUtils.createErrorContext('bloom-command-registration'));
        await ErrorUtils.showErrorMessage('An error occurred while executing the Bloom command. Check the output for details.');
      }
    });
  }

  /**
   * Clean up resources
   */
  dispose(): void {
    // Cleanup any resources if needed
    // Currently no persistent resources to clean up
  }
}
