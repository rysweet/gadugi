import { exec } from 'child_process';
import * as vscode from 'vscode';
import { WorktreeInfo, GitCommandResult } from '../types';
import { ErrorUtils } from '../utils/errorUtils';
import { PathUtils } from '../utils/pathUtils';

/**
 * Service for git operations and worktree management
 */
export class GitService {
  private workspaceRoot: string;

  constructor() {
    this.workspaceRoot = this.getWorkspaceRoot();
  }

  /**
   * Get the workspace root directory
   */
  private getWorkspaceRoot(): string {
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
      throw new Error('No workspace folder is open');
    }
    return vscode.workspace.workspaceFolders[0].uri.fsPath;
  }

  /**
   * Check if the current workspace is a git repository
   */
  async isGitRepository(): Promise<boolean> {
    try {
      const result = await this.executeGitCommand('rev-parse --git-dir');
      return result.success;
    } catch {
      return false;
    }
  }

  /**
   * Get all git worktrees in the repository
   */
  async getWorktrees(): Promise<WorktreeInfo[]> {
    try {
      const result = await this.executeGitCommand('worktree list --porcelain');
      if (!result.success || !result.output) {
        return [];
      }

      return this.parseWorktreeOutput(result.output);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('git-worktree-discovery'));
      return [];
    }
  }

  /**
   * Parse the output of 'git worktree list --porcelain'
   */
  private parseWorktreeOutput(output: string): WorktreeInfo[] {
    const worktrees: WorktreeInfo[] = [];
    const lines = output.split('\n').filter(line => line.trim());

    let currentWorktree: Partial<WorktreeInfo> = {};

    for (const line of lines) {
      const trimmed = line.trim();
      
      if (trimmed.startsWith('worktree ')) {
        // Save previous worktree if it exists
        if (currentWorktree.path) {
          worktrees.push(this.completeWorktreeInfo(currentWorktree));
        }
        
        // Start new worktree
        currentWorktree = {
          path: trimmed.substring('worktree '.length)
        };
      } else if (trimmed.startsWith('HEAD ')) {
        currentWorktree.head = trimmed.substring('HEAD '.length);
      } else if (trimmed.startsWith('branch ')) {
        const branchRef = trimmed.substring('branch '.length);
        currentWorktree.branch = branchRef.replace('refs/heads/', '');
      } else if (trimmed === 'bare') {
        currentWorktree.bare = true;
      } else if (trimmed === 'detached') {
        currentWorktree.detached = true;
      }
    }

    // Add the last worktree
    if (currentWorktree.path) {
      worktrees.push(this.completeWorktreeInfo(currentWorktree));
    }

    return worktrees;
  }

  /**
   * Complete worktree info with defaults
   */
  private completeWorktreeInfo(partial: Partial<WorktreeInfo>): WorktreeInfo {
    return {
      path: partial.path || '',
      head: partial.head || '',
      branch: partial.branch || 'HEAD',
      bare: partial.bare || false,
      detached: partial.detached || false
    };
  }

  /**
   * Get worktree information using the legacy format (fallback)
   */
  async getWorktreesLegacy(): Promise<WorktreeInfo[]> {
    try {
      const result = await this.executeGitCommand('worktree list');
      if (!result.success || !result.output) {
        return [];
      }

      return this.parseWorktreeOutputLegacy(result.output);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('git-worktree-discovery-legacy'));
      return [];
    }
  }

  /**
   * Parse the legacy output of 'git worktree list'
   */
  private parseWorktreeOutputLegacy(output: string): WorktreeInfo[] {
    const worktrees: WorktreeInfo[] = [];
    const lines = output.split('\n').filter(line => line.trim());

    for (const line of lines) {
      const parts = line.split(/\s+/);
      if (parts.length < 2) {continue;}

      const path = parts[0];
      const head = parts[1];
      const branch = parts.length > 2 ? parts[2].replace(/[[\]]/g, '') : 'HEAD';

      worktrees.push({
        path,
        head,
        branch,
        bare: false,
        detached: head !== branch
      });
    }

    return worktrees;
  }

  /**
   * Create a new worktree
   */
  async createWorktree(branch: string, path?: string): Promise<GitCommandResult> {
    try {
      const worktreePath = path || PathUtils.join(this.workspaceRoot, '.worktrees', branch);
      const command = `worktree add "${worktreePath}" ${branch}`;
      
      return await this.executeGitCommand(command);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('git-worktree-creation', { branch, path }));
      return { success: false, output: '', error: err.message };
    }
  }

  /**
   * Remove a worktree
   */
  async removeWorktree(path: string): Promise<GitCommandResult> {
    try {
      const command = `worktree remove "${path}"`;
      return await this.executeGitCommand(command);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('git-worktree-removal', { path }));
      return { success: false, output: '', error: err.message };
    }
  }

  /**
   * Get the current branch for a specific worktree
   */
  async getCurrentBranch(worktreePath?: string): Promise<string> {
    try {
      const result = await this.executeGitCommand('branch --show-current', worktreePath);
      return result.success ? result.output.trim() : 'unknown';
    } catch {
      return 'unknown';
    }
  }

  /**
   * Get the git status for a specific worktree
   */
  async getWorktreeStatus(worktreePath?: string): Promise<{ clean: boolean; changes: number }> {
    try {
      const result = await this.executeGitCommand('status --porcelain', worktreePath);
      if (!result.success) {
        return { clean: false, changes: 0 };
      }

      const changes = result.output.split('\n').filter(line => line.trim()).length;
      return { clean: changes === 0, changes };
    } catch {
      return { clean: false, changes: 0 };
    }
  }

  /**
   * Execute a git command
   */
  private executeGitCommand(command: string, cwd?: string): Promise<GitCommandResult> {
    const workingDirectory = cwd || this.workspaceRoot;
    const fullCommand = `git ${command}`;

    return new Promise((resolve) => {
      exec(fullCommand, { cwd: workingDirectory }, (error, stdout, stderr) => {
        if (error) {
          resolve({
            success: false,
            output: stdout || '',
            error: stderr || error.message
          });
        } else {
          resolve({
            success: true,
            output: stdout || '',
            error: stderr || undefined
          });
        }
      });
    });
  }

  /**
   * Validate git installation
   */
  async validateGitInstallation(): Promise<boolean> {
    try {
      const result = await this.executeGitCommand('--version');
      return result.success;
    } catch {
      return false;
    }
  }

  /**
   * Get git repository root
   */
  async getRepositoryRoot(): Promise<string> {
    try {
      const result = await this.executeGitCommand('rev-parse --show-toplevel');
      return result.success ? result.output.trim() : this.workspaceRoot;
    } catch {
      return this.workspaceRoot;
    }
  }

  /**
   * Check if a path is a valid worktree
   */
  async isValidWorktree(path: string): Promise<boolean> {
    try {
      const result = await this.executeGitCommand('rev-parse --git-dir', path);
      return result.success;
    } catch {
      return false;
    }
  }

  /**
   * Get worktree name for display purposes
   */
  getWorktreeDisplayName(worktree: WorktreeInfo): string {
    // If it's the main worktree (typically the repository root)
    if (PathUtils.areSamePath(worktree.path, this.workspaceRoot)) {
      return 'main';
    }

    // Use the branch name if available
    if (worktree.branch && worktree.branch !== 'HEAD') {
      return worktree.branch;
    }

    // Fall back to the directory name
    return PathUtils.getWorktreeName(worktree.path);
  }
}