import * as vscode from 'vscode';
import { GitService } from '../services/gitService';
import { ClaudeService } from '../services/claudeService';
import { UpdateManager } from '../services/updateManager';
import { ProcessUtils } from '../utils/processUtils';
import { ErrorUtils } from '../utils/errorUtils';
import { PathUtils } from '../utils/pathUtils';
// TimeUtils imported for potential future use
// import { TimeUtils } from '../utils/timeUtils';
import { WorktreeModel, ClaudeProcessModel, MonitorPanelStateModel } from '../models';
import { Worktree, ClaudeProcess, WorktreeStatus, ProcessStatus } from '../types';

/**
 * Tree data provider for the monitor panel
 */
export class MonitorTreeProvider implements vscode.TreeDataProvider<MonitorTreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<MonitorTreeItem | undefined | null | void> = new vscode.EventEmitter<MonitorTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<MonitorTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

  private gitService: GitService;
  private claudeService: ClaudeService;
  private updateManager: UpdateManager;
  private state: MonitorPanelStateModel;
  private updateSubscription?: () => void;

  constructor() {
    this.gitService = new GitService();
    this.claudeService = new ClaudeService();
    this.updateManager = UpdateManager.fromConfiguration();
    this.state = new MonitorPanelStateModel();

    this.setupUpdateSubscription();
  }

  /**
   * Setup automatic updates
   */
  private setupUpdateSubscription(): void {
    this.updateSubscription = this.updateManager.subscribe(async () => {
      await this.refreshData();
    });

    this.updateManager.start();
  }

  /**
   * Get tree item
   */
  getTreeItem(element: MonitorTreeItem): vscode.TreeItem {
    const treeItem = new vscode.TreeItem(
      element.label,
      element.collapsibleState || vscode.TreeItemCollapsibleState.None
    );

    treeItem.id = element.id;
    treeItem.description = element.description;
    treeItem.tooltip = element.tooltip;
    treeItem.contextValue = element.contextValue;
    treeItem.command = element.command;

    // Set icons based on context
    if (element.contextValue === 'worktree') {
      treeItem.iconPath = new vscode.ThemeIcon('folder');
      treeItem.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;
    } else if (element.contextValue === 'process') {
      treeItem.iconPath = new vscode.ThemeIcon('play');
      treeItem.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;
    } else if (element.contextValue === 'claudeProcess') {
      treeItem.iconPath = new vscode.ThemeIcon('play');
    } else if (element.contextValue === 'noClaudeProcess') {
      treeItem.iconPath = new vscode.ThemeIcon('stop');
    } else if (element.contextValue === 'processInfo') {
      treeItem.iconPath = new vscode.ThemeIcon('info');
    }

    return treeItem;
  }

  /**
   * Get children for tree item
   */
  async getChildren(element?: MonitorTreeItem): Promise<MonitorTreeItem[]> {
    try {
      if (!element) {
        // Root level - return main sections
        return this.getRootItems();
      }

      // Return children if they exist
      return element.children || [];
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-tree-get-children', { element }));
      return [];
    }
  }

  /**
   * Get root level items
   */
  private getRootItems(): MonitorTreeItem[] {
    const items: MonitorTreeItem[] = [];

    // Worktrees section
    const worktreeItems = Array.from(this.state.worktrees.values()).map(w => (w as WorktreeModel).toTreeItem());
    if (worktreeItems.length > 0) {
      items.push({
        id: 'worktrees-section',
        label: `📁 Worktrees (${worktreeItems.length})`,
        description: '',
        tooltip: `${worktreeItems.length} git worktrees found`,
        contextValue: 'worktreesSection',
        collapsibleState: vscode.TreeItemCollapsibleState.Expanded,
        children: worktreeItems
      });
    }

    // Processes section
    const processItems = Array.from(this.state.processes.values()).map(p => (p as ClaudeProcessModel).toTreeItem());
    if (processItems.length > 0) {
      items.push({
        id: 'processes-section',
        label: `⚡ Claude Processes (${processItems.length})`,
        description: '',
        tooltip: `${processItems.length} Claude processes running`,
        contextValue: 'processesSection',
        collapsibleState: vscode.TreeItemCollapsibleState.Expanded,
        children: processItems
      });
    }

    // If no data, show loading or empty state
    if (items.length === 0) {
      if (this.state.isRefreshing) {
        items.push({
          id: 'loading',
          label: '🔄 Loading...',
          description: 'Discovering worktrees and processes',
          tooltip: 'Please wait while data is being loaded',
          contextValue: 'loading'
        });
      } else {
        items.push({
          id: 'empty',
          label: '📭 No worktrees or processes found',
          description: 'Click refresh to try again',
          tooltip: 'No git worktrees or Claude processes detected',
          contextValue: 'empty'
        });
      }
    }

    return items;
  }

  /**
   * Refresh the tree data
   */
  async refresh(): Promise<void> {
    this.state.isRefreshing = true;
    this._onDidChangeTreeData.fire();

    try {
      await this.refreshData();
    } finally {
      this.state.isRefreshing = false;
      this._onDidChangeTreeData.fire();
    }
  }

  /**
   * Refresh underlying data
   */
  private async refreshData(): Promise<void> {
    try {
      // Refresh worktrees and processes in parallel
      const [worktrees, processes] = await Promise.all([
        this.refreshWorktrees(),
        this.refreshProcesses()
      ]);

      // Update state
      this.state.updateWorktrees(worktrees);
      this.state.updateProcesses(processes);
      this.state.associateProcessesWithWorktrees();

      // Update UI
      this._onDidChangeTreeData.fire();

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-refresh-data'));
    }
  }

  /**
   * Refresh worktree data
   */
  private async refreshWorktrees(): Promise<Worktree[]> {
    try {
      const worktreeInfos = await this.gitService.getWorktrees();
      const worktrees: Worktree[] = [];

      for (const info of worktreeInfos) {
        const worktree = new WorktreeModel({
          path: info.path,
          branch: info.branch,
          name: this.gitService.getWorktreeDisplayName(info),
          isMain: PathUtils.areSamePath(info.path, await this.gitService.getRepositoryRoot()),
          status: WorktreeStatus.Active
        });

        worktrees.push(worktree);
      }

      return worktrees;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-refresh-worktrees'));
      return [];
    }
  }

  /**
   * Refresh process data
   */
  private async refreshProcesses(): Promise<ClaudeProcess[]> {
    try {
      const processInfos = await ProcessUtils.getClaudeProcesses();
      const processes: ClaudeProcess[] = [];

      for (const info of processInfos) {
        const process = new ClaudeProcessModel({
          pid: info.pid,
          command: info.command,
          workingDirectory: info.workingDirectory,
          startTime: info.startTime,
          status: ProcessStatus.Running,
          memoryUsage: info.memoryUsage,
          cpuUsage: info.cpuUsage
        });

        processes.push(process);
      }

      return processes;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-refresh-processes'));
      return [];
    }
  }

  /**
   * Launch Claude in a worktree
   */
  async launchClaudeInWorktree(worktreeId: string): Promise<void> {
    try {
      const worktree = this.state.worktrees.get(worktreeId);
      if (!worktree) {
        throw new Error(`Worktree not found: ${worktreeId}`);
      }

      const command = this.claudeService.getClaudeCommand();
      const result = await this.claudeService.launchClaude(worktree.path, command);

      if (result.success) {
        await ErrorUtils.showInfoMessage(`Claude launched successfully in ${worktree.name}`);
        await this.refresh();
      } else {
        throw new Error(result.error || 'Failed to launch Claude');
      }

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-launch-claude', { worktreeId }));
      await ErrorUtils.showErrorMessage(`Failed to launch Claude: ${err.message}`);
    }
  }

  /**
   * Terminate a Claude process
   */
  async terminateProcess(processId: string): Promise<void> {
    try {
      const process = this.state.processes.get(processId);
      if (!process) {
        throw new Error(`Process not found: ${processId}`);
      }

      const confirmation = await vscode.window.showWarningMessage(
        `Are you sure you want to terminate Claude process ${process.pid}?`,
        'Yes',
        'No'
      );

      if (confirmation !== 'Yes') {
        return;
      }

      const result = await this.claudeService.killClaudeProcess(process.pid);

      if (result) {
        await ErrorUtils.showInfoMessage(`Process ${process.pid} terminated successfully`);
        await this.refresh();
      } else {
        throw new Error('Failed to terminate process');
      }

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-terminate-process', { processId }));
      await ErrorUtils.showErrorMessage(`Failed to terminate process: ${err.message}`);
    }
  }

  /**
   * Navigate to worktree
   */
  async navigateToWorktree(worktreeId: string): Promise<void> {
    try {
      const worktree = this.state.worktrees.get(worktreeId);
      if (!worktree) {
        throw new Error(`Worktree not found: ${worktreeId}`);
      }

      // Open the worktree folder in VS Code
      const uri = vscode.Uri.file(worktree.path);
      await vscode.commands.executeCommand('vscode.openFolder', uri, { forceNewWindow: false });

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('monitor-navigate-worktree', { worktreeId }));
      await ErrorUtils.showErrorMessage(`Failed to navigate to worktree: ${err.message}`);
    }
  }

  /**
   * Get panel statistics
   */
  getStats() {
    return this.state.getStats();
  }

  /**
   * Dispose resources
   */
  dispose(): void {
    if (this.updateSubscription) {
      this.updateSubscription();
    }
    this.updateManager.dispose();
  }

  /**
   * Register commands for tree interactions
   */
  static registerCommands(context: vscode.ExtensionContext, provider: MonitorTreeProvider): void {
    // Refresh command
    context.subscriptions.push(
      vscode.commands.registerCommand('gadugi.refresh', async () => {
        await provider.refresh();
      })
    );

    // Launch Claude command
    context.subscriptions.push(
      vscode.commands.registerCommand('gadugi.launchClaude', async (item: MonitorTreeItem) => {
        if (item && item.contextValue === 'worktree') {
          await provider.launchClaudeInWorktree(item.id);
        }
      })
    );

    // Terminate process command
    context.subscriptions.push(
      vscode.commands.registerCommand('gadugi.terminateProcess', async (item: MonitorTreeItem) => {
        if (item && item.contextValue === 'process') {
          await provider.terminateProcess(item.id);
        }
      })
    );

    // Navigate to worktree command
    context.subscriptions.push(
      vscode.commands.registerCommand('gadugi.navigateToWorktree', async (item: MonitorTreeItem) => {
        if (item && item.contextValue === 'worktree') {
          await provider.navigateToWorktree(item.id);
        }
      })
    );
  }
}

/**
 * Tree item interface for monitor panel
 */
export interface MonitorTreeItem {
  id: string;
  label: string;
  description?: string;
  tooltip?: string;
  contextValue: string;
  iconPath?: string | vscode.ThemeIcon;
  collapsibleState?: vscode.TreeItemCollapsibleState;
  children?: MonitorTreeItem[];
  command?: vscode.Command;
}
