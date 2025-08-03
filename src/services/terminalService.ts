import * as vscode from 'vscode';
// LaunchConfig and PathUtils imported for potential future use
// import { LaunchConfig } from '../types';
import { ErrorUtils } from '../utils/errorUtils';
// import { PathUtils } from '../utils/pathUtils';

/**
 * Service for VS Code terminal management
 */
export class TerminalService {
  private terminals: Map<string, vscode.Terminal> = new Map();

  /**
   * Create a new terminal for a worktree
   */
  async createWorktreeTerminal(
    worktreePath: string,
    worktreeName: string,
    command?: string
  ): Promise<vscode.Terminal | undefined> {
    try {
      const terminalName = `Claude: ${worktreeName}`;
      
      // Check if terminal already exists
      const existingTerminal = this.findTerminalByName(terminalName);
      if (existingTerminal) {
        existingTerminal.show();
        return existingTerminal;
      }

      // Create new terminal
      const terminal = vscode.window.createTerminal({
        name: terminalName,
        cwd: worktreePath,
        hideFromUser: false
      });

      // Store reference
      this.terminals.set(terminalName, terminal);

      // Show the terminal
      terminal.show();

      // Execute command if provided
      if (command) {
        // Give the terminal a moment to initialize
        setTimeout(() => {
          terminal.sendText(command);
        }, 500);
      }

      ErrorUtils.logInfo(`Created terminal "${terminalName}" in ${worktreePath}`, 'terminal-creation');
      return terminal;

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('terminal-creation', { worktreePath, worktreeName }));
      return undefined;
    }
  }

  /**
   * Find an existing terminal by name
   */
  private findTerminalByName(name: string): vscode.Terminal | undefined {
    // Check our cached terminals first
    const cachedTerminal = this.terminals.get(name);
    if (cachedTerminal && cachedTerminal.exitStatus === undefined) {
      return cachedTerminal;
    }

    // Search through all VS Code terminals
    const allTerminals = vscode.window.terminals;
    const terminal = allTerminals.find(t => t.name === name && t.exitStatus === undefined);
    
    if (terminal) {
      this.terminals.set(name, terminal);
    }

    return terminal;
  }

  /**
   * Create multiple terminals for worktrees
   */
  async createTerminalsForWorktrees(
    worktrees: Array<{ path: string; name: string }>,
    command?: string
  ): Promise<{ success: number; failed: number; errors: string[] }> {
    const results = {
      success: 0,
      failed: 0,
      errors: [] as string[]
    };

    for (const worktree of worktrees) {
      const terminal = await this.createWorktreeTerminal(worktree.path, worktree.name, command);
      
      if (terminal) {
        results.success++;
      } else {
        results.failed++;
        results.errors.push(`Failed to create terminal for ${worktree.name}`);
      }

      // Small delay between terminal creations to avoid overwhelming the system
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    return results;
  }

  /**
   * Execute a command in a specific terminal
   */
  async executeCommandInTerminal(terminalName: string, command: string): Promise<boolean> {
    try {
      const terminal = this.findTerminalByName(terminalName);
      if (!terminal) {
        ErrorUtils.logWarning(`Terminal "${terminalName}" not found`, 'command-execution');
        return false;
      }

      terminal.sendText(command);
      terminal.show();
      
      ErrorUtils.logInfo(`Executed command in terminal "${terminalName}": ${command}`, 'command-execution');
      return true;

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('command-execution', { terminalName, command }));
      return false;
    }
  }

  /**
   * Launch Claude Code in a terminal
   */
  async launchClaudeInTerminal(
    worktreePath: string,
    worktreeName: string,
    claudeCommand: string = 'claude --resume'
  ): Promise<vscode.Terminal | undefined> {
    return await this.createWorktreeTerminal(worktreePath, worktreeName, claudeCommand);
  }

  /**
   * Get all active terminals
   */
  getActiveTerminals(): vscode.Terminal[] {
    return vscode.window.terminals.filter(terminal => terminal.exitStatus === undefined);
  }

  /**
   * Get terminals that match the Claude naming pattern
   */
  getClaudeTerminals(): vscode.Terminal[] {
    return this.getActiveTerminals().filter(terminal => 
      terminal.name.startsWith('Claude:')
    );
  }

  /**
   * Close a terminal by name
   */
  async closeTerminal(terminalName: string): Promise<boolean> {
    try {
      const terminal = this.findTerminalByName(terminalName);
      if (!terminal) {
        return false;
      }

      terminal.dispose();
      this.terminals.delete(terminalName);
      
      ErrorUtils.logInfo(`Closed terminal "${terminalName}"`, 'terminal-management');
      return true;

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('terminal-closure', { terminalName }));
      return false;
    }
  }

  /**
   * Close all Claude terminals
   */
  async closeAllClaudeTerminals(): Promise<number> {
    const claudeTerminals = this.getClaudeTerminals();
    let closed = 0;

    for (const terminal of claudeTerminals) {
      try {
        terminal.dispose();
        this.terminals.delete(terminal.name);
        closed++;
      } catch (error) {
        ErrorUtils.logWarning(`Failed to close terminal "${terminal.name}"`, 'terminal-cleanup');
      }
    }

    ErrorUtils.logInfo(`Closed ${closed} Claude terminals`, 'terminal-cleanup');
    return closed;
  }

  /**
   * Navigate to a worktree directory in a new terminal
   */
  async navigateToWorktree(worktreePath: string, worktreeName: string): Promise<vscode.Terminal | undefined> {
    try {
      const terminalName = `Navigate: ${worktreeName}`;
      
      const terminal = vscode.window.createTerminal({
        name: terminalName,
        cwd: worktreePath
      });

      terminal.show();
      
      ErrorUtils.logInfo(`Opened navigation terminal for ${worktreeName}`, 'navigation');
      return terminal;

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('navigation', { worktreePath, worktreeName }));
      return undefined;
    }
  }

  /**
   * Get terminal statistics
   */
  getTerminalStats(): { total: number; claude: number; active: number } {
    const allTerminals = this.getActiveTerminals();
    const claudeTerminals = this.getClaudeTerminals();

    return {
      total: vscode.window.terminals.length,
      claude: claudeTerminals.length,
      active: allTerminals.length
    };
  }

  /**
   * Validate terminal creation capabilities
   */
  async validateTerminalSupport(): Promise<{ supported: boolean; issues: string[] }> {
    const issues: string[] = [];

    try {
      // Try to create a test terminal
      const testTerminal = vscode.window.createTerminal({
        name: 'Gadugi-Test',
        hideFromUser: true
      });

      // Clean up immediately
      testTerminal.dispose();

    } catch (error) {
      issues.push('Unable to create terminals in VS Code');
    }

    // Check workspace requirements
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
      issues.push('No workspace folder is open');
    }

    return {
      supported: issues.length === 0,
      issues
    };
  }

  // Unique terminal name generation removed for simplicity
  // Can be added back if needed for conflict resolution

  /**
   * Clean up closed terminals from our cache
   */
  cleanupTerminalCache(): void {
    const activeTerminalNames = new Set(
      vscode.window.terminals
        .filter(t => t.exitStatus === undefined)
        .map(t => t.name)
    );

    for (const [name, terminal] of this.terminals.entries()) {
      if (!activeTerminalNames.has(name) || terminal.exitStatus !== undefined) {
        this.terminals.delete(name);
      }
    }
  }

  /**
   * Setup terminal event listeners
   */
  setupEventListeners(): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];

    // Listen for terminal closures to clean up our cache
    disposables.push(
      vscode.window.onDidCloseTerminal((terminal) => {
        this.terminals.delete(terminal.name);
        ErrorUtils.logInfo(`Terminal "${terminal.name}" was closed`, 'terminal-management');
      })
    );

    // Listen for terminal creation
    disposables.push(
      vscode.window.onDidOpenTerminal((terminal) => {
        ErrorUtils.logInfo(`Terminal "${terminal.name}" was opened`, 'terminal-management');
      })
    );

    return disposables;
  }
}