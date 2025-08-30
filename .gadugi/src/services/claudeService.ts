import { exec } from 'child_process';
import * as vscode from 'vscode';
import { LaunchConfig } from '../types';
import { ErrorUtils } from '../utils/errorUtils';
import { ProcessUtils } from '../utils/processUtils';

/**
 * Service for Claude Code integration
 */
export class ClaudeService {
  private static readonly DEFAULT_COMMAND = 'claude --resume';
  private static readonly TIMEOUT_MS = 10000; // 10 seconds

  /**
   * Check if Claude Code is installed and accessible
   */
  async isClaudeInstalled(): Promise<{ installed: boolean; version?: string; error?: string }> {
    try {
      return new Promise((resolve) => {
        exec('claude --version', { timeout: ClaudeService.TIMEOUT_MS }, (error, stdout, stderr) => {
          if (error) {
            resolve({
              installed: false,
              error: `Claude not found: ${error.message}`
            });
          } else {
            const version = stdout.trim() || stderr.trim();
            resolve({
              installed: true,
              version: version || 'Unknown version'
            });
          }
        });
      });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      return {
        installed: false,
        error: err.message
      };
    }
  }

  /**
   * Launch Claude Code in a specific directory
   */
  async launchClaude(
    workingDirectory: string,
    command: string = ClaudeService.DEFAULT_COMMAND
  ): Promise<{ success: boolean; pid?: number; error?: string }> {
    try {
      const [cmd, ...args] = command.split(' ');

      return await ProcessUtils.startProcess(cmd, args, workingDirectory);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('claude-launch', { workingDirectory, command }));
      return {
        success: false,
        error: err.message
      };
    }
  }

  /**
   * Launch Claude Code using VS Code terminal
   */
  async launchClaudeInTerminal(
    terminal: vscode.Terminal,
    command: string = ClaudeService.DEFAULT_COMMAND
  ): Promise<void> {
    try {
      // Send the Claude command to the terminal
      terminal.sendText(command);

      ErrorUtils.logInfo(`Launched Claude in terminal with command: ${command}`, 'claude-terminal-launch');
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('claude-terminal-launch', { command }));
      throw err;
    }
  }

  /**
   * Get all running Claude processes
   */
  async getRunningClaudeProcesses() {
    try {
      return await ProcessUtils.getClaudeProcesses();
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('claude-process-discovery'));
      return [];
    }
  }

  /**
   * Kill a Claude process
   */
  async killClaudeProcess(pid: number): Promise<boolean> {
    try {
      const result = await ProcessUtils.killProcess(pid);

      if (result) {
        ErrorUtils.logInfo(`Successfully killed Claude process ${pid}`, 'claude-process-management');
      } else {
        ErrorUtils.logWarning(`Failed to kill Claude process ${pid}`, 'claude-process-management');
      }

      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('claude-process-termination', { pid }));
      return false;
    }
  }

  /**
   * Check if a Claude process is still running
   */
  async isClaudeProcessRunning(pid: number): Promise<boolean> {
    try {
      return await ProcessUtils.isProcessRunning(pid);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('claude-process-check', { pid }));
      return false;
    }
  }

  /**
   * Validate Claude installation and show user feedback
   */
  async validateClaudeInstallation(): Promise<boolean> {
    const result = await this.isClaudeInstalled();

    if (!result.installed) {
      const message = 'Claude Code is not installed or not accessible. Please install Claude Code CLI to use this extension.';
      const action = await ErrorUtils.showErrorMessage(message, 'Install Guide', 'Dismiss');

      if (action === 'Install Guide') {
        vscode.env.openExternal(vscode.Uri.parse('https://claude.ai/docs/cli'));
      }

      return false;
    }

    ErrorUtils.logInfo(`Claude Code is installed: ${result.version}`, 'claude-validation');
    return true;
  }

  /**
   * Get the default Claude command from configuration
   */
  getClaudeCommand(): string {
    const config = vscode.workspace.getConfiguration('gadugi');
    return config.get<string>('claudeCommand', ClaudeService.DEFAULT_COMMAND);
  }

  /**
   * Test Claude command execution
   */
  async testClaudeCommand(command: string = this.getClaudeCommand()): Promise<{ success: boolean; output?: string; error?: string }> {
    try {
      return new Promise((resolve) => {
        // Test with --help flag to avoid actually starting Claude
        const testCommand = command.replace('--resume', '--help');

        exec(testCommand, { timeout: ClaudeService.TIMEOUT_MS }, (error, stdout, stderr) => {
          if (error) {
            resolve({
              success: false,
              error: error.message
            });
          } else {
            resolve({
              success: true,
              output: stdout || stderr
            });
          }
        });
      });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      return {
        success: false,
        error: err.message
      };
    }
  }

  /**
   * Get Claude process information by PID
   */
  async getClaudeProcessInfo(pid: number) {
    try {
      const processes = await this.getRunningClaudeProcesses();
      return processes.find(p => p.pid === pid);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('claude-process-info', { pid }));
      return undefined;
    }
  }

  /**
   * Monitor Claude process health
   */
  async monitorClaudeProcessHealth(pid: number, callback: (isRunning: boolean) => void): Promise<() => void> {
    const interval = setInterval(async () => {
      const isRunning = await this.isClaudeProcessRunning(pid);
      callback(isRunning);

      if (!isRunning) {
        clearInterval(interval);
      }
    }, 5000); // Check every 5 seconds

    // Return cleanup function
    return () => clearInterval(interval);
  }

  /**
   * Get Claude workspace information if available
   */
  async getClaudeWorkspaceInfo(workingDirectory: string): Promise<{ hasClaudeConfig: boolean; configPath?: string }> {
    try {
      const fs = require('fs');
      const path = require('path');

      // Check for common Claude configuration files
      const configFiles = ['.claude', '.claude.json', 'claude.json'];

      for (const configFile of configFiles) {
        const configPath = path.join(workingDirectory, configFile);
        if (fs.existsSync(configPath)) {
          return {
            hasClaudeConfig: true,
            configPath
          };
        }
      }

      return { hasClaudeConfig: false };
    } catch (error) {
      return { hasClaudeConfig: false };
    }
  }

  /**
   * Create a launch configuration for Claude
   */
  createLaunchConfig(
    workingDirectory: string,
    command: string = this.getClaudeCommand()
  ): LaunchConfig {
    const [cmd, ...args] = command.split(' ');

    return {
      command: cmd,
      args,
      workingDirectory,
      env: process.env as Record<string, string>
    };
  }

  /**
   * Batch launch Claude in multiple directories
   */
  async batchLaunchClaude(
    directories: string[],
    command: string = this.getClaudeCommand()
  ): Promise<{ successful: number; failed: number; pids: number[]; errors: string[] }> {
    const results = {
      successful: 0,
      failed: 0,
      pids: [] as number[],
      errors: [] as string[]
    };

    for (const directory of directories) {
      try {
        const result = await this.launchClaude(directory, command);

        if (result.success && result.pid) {
          results.successful++;
          results.pids.push(result.pid);
        } else {
          results.failed++;
          results.errors.push(result.error || `Failed to launch in ${directory}`);
        }

        // Small delay between launches to avoid overwhelming the system
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (error) {
        results.failed++;
        results.errors.push(`Error launching in ${directory}: ${error}`);
      }
    }

    return results;
  }

  /**
   * Get Claude process statistics
   */
  async getClaudeStats(): Promise<{
    totalProcesses: number;
    runningProcesses: number;
    avgRuntime: number;
    totalMemoryUsage: number;
  }> {
    try {
      const processes = await this.getRunningClaudeProcesses();
      const now = new Date();

      let totalRuntime = 0;
      let totalMemory = 0;
      let runningCount = 0;

      for (const process of processes) {
        const isRunning = await this.isClaudeProcessRunning(process.pid);
        if (isRunning) {
          runningCount++;
          totalRuntime += now.getTime() - process.startTime.getTime();
          if (process.memoryUsage) {
            totalMemory += process.memoryUsage;
          }
        }
      }

      return {
        totalProcesses: processes.length,
        runningProcesses: runningCount,
        avgRuntime: runningCount > 0 ? totalRuntime / runningCount : 0,
        totalMemoryUsage: totalMemory
      };
    } catch (error) {
      return {
        totalProcesses: 0,
        runningProcesses: 0,
        avgRuntime: 0,
        totalMemoryUsage: 0
      };
    }
  }
}
