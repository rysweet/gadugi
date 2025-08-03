import * as vscode from 'vscode';
import { MonitorTreeProvider } from './monitorTreeProvider';
import { ErrorUtils } from '../utils/errorUtils';

/**
 * Main monitor panel controller for the Gadugi VS Code extension
 */
export class MonitorPanel {
  private treeDataProvider: MonitorTreeProvider;
  private treeView: vscode.TreeView<any>;
  private disposables: vscode.Disposable[] = [];

  constructor(context: vscode.ExtensionContext) {
    this.treeDataProvider = new MonitorTreeProvider();
    
    // Create tree view
    this.treeView = vscode.window.createTreeView('gadugi.monitor', {
      treeDataProvider: this.treeDataProvider,
      showCollapseAll: true,
      canSelectMany: false
    });

    // Setup tree view
    this.setupTreeView();
    
    // Register commands
    MonitorTreeProvider.registerCommands(context, this.treeDataProvider);
    
    // Setup event listeners
    this.setupEventListeners();

    ErrorUtils.logInfo('Monitor panel initialized', 'monitor-panel');
  }

  /**
   * Setup tree view properties and behavior
   */
  private setupTreeView(): void {
    // Set initial title
    this.updateTitle();

    // Setup tree view selection handling
    this.disposables.push(
      this.treeView.onDidChangeSelection((event) => {
        this.handleSelectionChange(event.selection);
      })
    );

    // Setup tree view visibility handling
    this.disposables.push(
      this.treeView.onDidChangeVisibility((event) => {
        this.handleVisibilityChange(event.visible);
      })
    );

    // Setup tree view expansion handling
    this.disposables.push(
      this.treeView.onDidExpandElement((event) => {
        ErrorUtils.logInfo(`Expanded tree element: ${event.element.label}`, 'monitor-panel');
      })
    );

    this.disposables.push(
      this.treeView.onDidCollapseElement((event) => {
        ErrorUtils.logInfo(`Collapsed tree element: ${event.element.label}`, 'monitor-panel');
      })
    );
  }

  /**
   * Setup event listeners
   */
  private setupEventListeners(): void {
    // Listen for configuration changes
    this.disposables.push(
      vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration('gadugi')) {
          this.handleConfigurationChange();
        }
      })
    );

    // Listen for workspace changes
    this.disposables.push(
      vscode.workspace.onDidChangeWorkspaceFolders(() => {
        this.handleWorkspaceChange();
      })
    );

    // Refresh panel periodically to update title
    const titleUpdateInterval = setInterval(() => {
      this.updateTitle();
    }, 10000); // Every 10 seconds

    this.disposables.push(new vscode.Disposable(() => {
      clearInterval(titleUpdateInterval);
    }));
  }

  /**
   * Handle tree view selection changes
   */
  private handleSelectionChange(selection: readonly any[]): void {
    if (selection.length > 0) {
      const item = selection[0];
      ErrorUtils.logInfo(`Selected tree item: ${item.label} (${item.contextValue})`, 'monitor-panel');
      
      // Update status bar or show additional info based on selection
      this.updateStatusForSelection(item);
    }
  }

  /**
   * Handle tree view visibility changes
   */
  private handleVisibilityChange(visible: boolean): void {
    ErrorUtils.logInfo(`Monitor panel visibility changed: ${visible}`, 'monitor-panel');
    
    if (visible) {
      // Panel became visible - might want to refresh data
      this.treeDataProvider.refresh();
    }
  }

  /**
   * Handle configuration changes
   */
  private handleConfigurationChange(): void {
    ErrorUtils.logInfo('Configuration changed, refreshing monitor panel', 'monitor-panel');
    this.treeDataProvider.refresh();
  }

  /**
   * Handle workspace changes
   */
  private handleWorkspaceChange(): void {
    ErrorUtils.logInfo('Workspace changed, refreshing monitor panel', 'monitor-panel');
    this.treeDataProvider.refresh();
  }

  /**
   * Update panel title with current statistics
   */
  private updateTitle(): void {
    try {
      const stats = this.treeDataProvider.getStats();
      const title = `Worktrees: ${stats.activeWorktrees}/${stats.totalWorktrees} | Processes: ${stats.runningProcesses}/${stats.totalProcesses}`;
      
      this.treeView.title = title;
      this.treeView.description = `Last update: ${stats.lastUpdateTime}`;
    } catch (error) {
      // Fallback title if stats unavailable
      this.treeView.title = 'Worktree & Process Monitor';
    }
  }

  /**
   * Update status for selected item
   */
  private updateStatusForSelection(item: any): void {
    let statusText = '';
    
    switch (item.contextValue) {
      case 'worktree':
        statusText = `Worktree: ${item.label}`;
        break;
      case 'process':
        statusText = `Claude Process: ${item.label}`;
        break;
      case 'claudeProcess':
        statusText = `Claude running in worktree`;
        break;
      case 'noClaudeProcess':
        statusText = `No Claude process in worktree`;
        break;
      default:
        statusText = `Selected: ${item.label}`;
    }

    // Could update status bar here if needed
    ErrorUtils.logInfo(statusText, 'monitor-panel-selection');
  }

  /**
   * Refresh the panel data
   */
  async refresh(): Promise<void> {
    try {
      await this.treeDataProvider.refresh();
      this.updateTitle();
      ErrorUtils.logInfo('Monitor panel refreshed', 'monitor-panel');
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-panel-refresh'));
      await ErrorUtils.showErrorMessage('Failed to refresh monitor panel');
    }
  }

  /**
   * Show the panel
   */
  show(): void {
    this.treeView.reveal(undefined, { select: false, focus: true });
  }

  /**
   * Get the tree view instance
   */
  getTreeView(): vscode.TreeView<any> {
    return this.treeView;
  }

  /**
   * Get the tree data provider
   */
  getTreeDataProvider(): MonitorTreeProvider {
    return this.treeDataProvider;
  }

  /**
   * Check if panel is visible
   */
  isVisible(): boolean {
    return this.treeView.visible;
  }

  /**
   * Get panel statistics
   */
  getStats() {
    return this.treeDataProvider.getStats();
  }

  /**
   * Export panel data for debugging
   */
  exportData(): any {
    const stats = this.getStats();
    return {
      visible: this.isVisible(),
      title: this.treeView.title,
      description: this.treeView.description,
      stats,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Handle panel commands
   */
  async executeCommand(command: string, ...args: any[]): Promise<void> {
    try {
      switch (command) {
        case 'refresh':
          await this.refresh();
          break;
        case 'show':
          this.show();
          break;
        case 'export-data':
          const data = this.exportData();
          ErrorUtils.logInfo(`Panel data: ${JSON.stringify(data, null, 2)}`, 'monitor-panel');
          break;
        default:
          ErrorUtils.logWarning(`Unknown panel command: ${command}`, 'monitor-panel');
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-panel-command', { command, args }));
    }
  }

  // Keyboard shortcuts functionality removed for simplicity
  // Can be added back if needed for custom keybindings

  /**
   * Validate panel prerequisites
   */
  async validatePrerequisites(): Promise<{ valid: boolean; issues: string[] }> {
    const issues: string[] = [];

    try {
      // Check workspace
      if (!vscode.workspace.workspaceFolders) {
        issues.push('No workspace folder is open');
      }

      // Check git repository
      // This could be expanded with more validation
      
    } catch (error) {
      issues.push('Failed to validate prerequisites');
    }

    return {
      valid: issues.length === 0,
      issues
    };
  }

  /**
   * Dispose all resources
   */
  dispose(): void {
    this.treeDataProvider.dispose();
    
    for (const disposable of this.disposables) {
      disposable.dispose();
    }
    
    this.disposables = [];
    
    ErrorUtils.logInfo('Monitor panel disposed', 'monitor-panel');
  }

  /**
   * Create and register the monitor panel
   */
  static create(context: vscode.ExtensionContext): MonitorPanel {
    const panel = new MonitorPanel(context);
    
    // Add to context subscriptions for automatic disposal
    context.subscriptions.push(panel);
    
    return panel;
  }
}