import * as vscode from 'vscode';
import { ErrorContext, PerformanceMetrics } from '../types';

/**
 * Error handling and logging utilities for the Gadugi VS Code extension
 */
export class ErrorUtils {
  private static readonly outputChannel = vscode.window.createOutputChannel('Gadugi');

  /**
   * Log an error with context information
   */
  static logError(error: Error, context: ErrorContext): void {
    const timestamp = context.timestamp.toISOString();
    const message = `[${timestamp}] ERROR in ${context.operation}: ${error.message}`;
    
    console.error(message, error);
    ErrorUtils.outputChannel.appendLine(message);
    
    if (context.details) {
      ErrorUtils.outputChannel.appendLine(`Details: ${JSON.stringify(context.details, null, 2)}`);
    }
    
    ErrorUtils.outputChannel.appendLine(`Stack: ${error.stack || 'No stack trace available'}`);
    ErrorUtils.outputChannel.appendLine('---');
  }

  /**
   * Log a warning message
   */
  static logWarning(message: string, operation?: string): void {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] WARNING${operation ? ` in ${operation}` : ''}: ${message}`;
    
    console.warn(logMessage);
    ErrorUtils.outputChannel.appendLine(logMessage);
  }

  /**
   * Log an info message
   */
  static logInfo(message: string, operation?: string): void {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] INFO${operation ? ` in ${operation}` : ''}: ${message}`;
    
    console.log(logMessage);
    ErrorUtils.outputChannel.appendLine(logMessage);
  }

  /**
   * Show an error message to the user
   */
  static async showErrorMessage(message: string, ...actions: string[]): Promise<string | undefined> {
    return await vscode.window.showErrorMessage(message, ...actions);
  }

  /**
   * Show a warning message to the user
   */
  static async showWarningMessage(message: string, ...actions: string[]): Promise<string | undefined> {
    return await vscode.window.showWarningMessage(message, ...actions);
  }

  /**
   * Show an info message to the user
   */
  static async showInfoMessage(message: string, ...actions: string[]): Promise<string | undefined> {
    return await vscode.window.showInformationMessage(message, ...actions);
  }

  /**
   * Handle an error gracefully with user feedback
   */
  static async handleError(error: Error, context: ErrorContext, showToUser: boolean = true): Promise<void> {
    ErrorUtils.logError(error, context);

    if (showToUser) {
      const userMessage = ErrorUtils.getUserFriendlyMessage(error, context);
      const action = await ErrorUtils.showErrorMessage(userMessage, 'Show Details', 'Dismiss');
      
      if (action === 'Show Details') {
        ErrorUtils.outputChannel.show();
      }
    }
  }

  /**
   * Get a user-friendly error message
   */
  private static getUserFriendlyMessage(error: Error, context: ErrorContext): string {
    switch (context.operation) {
      case 'git-worktree-discovery':
        return 'Failed to discover git worktrees. Please ensure you are in a git repository.';
      case 'process-monitoring':
        return 'Failed to monitor processes. Some process information may be unavailable.';
      case 'claude-launch':
        return 'Failed to launch Claude Code. Please ensure Claude is installed and accessible.';
      case 'terminal-creation':
        return 'Failed to create terminal. Please check VS Code terminal settings.';
      default:
        return `An error occurred during ${context.operation}: ${error.message}`;
    }
  }

  /**
   * Wrap a function with error handling
   */
  static withErrorHandling<T extends (...args: any[]) => any>(
    func: T,
    operation: string,
    showToUser: boolean = true
  ): (...args: Parameters<T>) => Promise<ReturnType<T> | undefined> {
    return async (...args: Parameters<T>) => {
      try {
        return await func(...args);
      } catch (error) {
        await ErrorUtils.handleError(
          error instanceof Error ? error : new Error(String(error)),
          {
            operation,
            details: { args },
            timestamp: new Date()
          },
          showToUser
        );
        return undefined;
      }
    };
  }

  /**
   * Performance monitoring wrapper
   */
  static withPerformanceMonitoring<T extends (...args: any[]) => any>(
    func: T,
    operationName: string
  ): (...args: Parameters<T>) => Promise<ReturnType<T>> {
    return async (...args: Parameters<T>) => {
      const startTime = Date.now();
      let success = false;
      
      try {
        const result = await func(...args);
        success = true;
        return result;
      } finally {
        const duration = Date.now() - startTime;
        const metrics: PerformanceMetrics = {
          operationName,
          duration,
          timestamp: new Date(),
          success
        };
        
        ErrorUtils.logPerformanceMetrics(metrics);
      }
    };
  }

  /**
   * Log performance metrics
   */
  private static logPerformanceMetrics(metrics: PerformanceMetrics): void {
    const message = `[PERF] ${metrics.operationName}: ${metrics.duration}ms (${metrics.success ? 'SUCCESS' : 'FAILED'})`;
    
    if (metrics.duration > 1000) {
      ErrorUtils.logWarning(`Slow operation detected: ${message}`, 'performance-monitoring');
    } else {
      ErrorUtils.outputChannel.appendLine(message);
    }
  }

  /**
   * Validate required dependencies
   */
  static async validateDependencies(): Promise<string[]> {
    const issues: string[] = [];

    // Check if git is available
    try {
      const { execSync } = require('child_process');
      execSync('git --version', { stdio: 'ignore' });
    } catch {
      issues.push('Git is not installed or not in PATH');
    }

    // Check if we're in a git repository
    if (vscode.workspace.workspaceFolders) {
      try {
        const { execSync } = require('child_process');
        const workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;
        execSync('git rev-parse --git-dir', { cwd: workspaceRoot, stdio: 'ignore' });
      } catch {
        issues.push('Current workspace is not a git repository');
      }
    } else {
      issues.push('No workspace folder is open');
    }

    return issues;
  }

  /**
   * Create an error context object
   */
  static createErrorContext(operation: string, details?: any): ErrorContext {
    return {
      operation,
      details,
      timestamp: new Date()
    };
  }

  /**
   * Show the output channel
   */
  static showOutput(): void {
    ErrorUtils.outputChannel.show();
  }

  /**
   * Clear the output channel
   */
  static clearOutput(): void {
    ErrorUtils.outputChannel.clear();
  }
}