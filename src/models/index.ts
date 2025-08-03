import { 
  Worktree, 
  ClaudeProcess, 
  MonitorPanelState, 
  WorktreeStatus, 
  ProcessStatus,
  MonitorTreeItem 
} from '../types';
import { TimeUtils } from '../utils/timeUtils';
import { PathUtils } from '../utils/pathUtils';

/**
 * Data models for the monitor panel
 */

export class WorktreeModel implements Worktree {
  id: string;
  name: string;
  path: string;
  branch: string;
  isMain: boolean;
  hasClaudeProcess: boolean;
  claudeProcessId?: number;
  status: WorktreeStatus;

  constructor(data: Partial<Worktree>) {
    this.id = data.id || this.generateId();
    this.name = data.name || PathUtils.getWorktreeName(data.path || '');
    this.path = data.path || '';
    this.branch = data.branch || 'unknown';
    this.isMain = data.isMain || false;
    this.hasClaudeProcess = data.hasClaudeProcess || false;
    this.claudeProcessId = data.claudeProcessId;
    this.status = data.status || WorktreeStatus.Active;
  }

  private generateId(): string {
    return `worktree-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Update the worktree with new data
   */
  update(data: Partial<Worktree>): void {
    Object.assign(this, data);
  }

  /**
   * Get display name for the worktree
   */
  getDisplayName(): string {
    return this.isMain ? `${this.name} (main)` : this.name;
  }

  /**
   * Get status icon
   */
  getStatusIcon(): string {
    switch (this.status) {
      case WorktreeStatus.Active:
        return this.hasClaudeProcess ? '⚡' : '📁';
      case WorktreeStatus.Inactive:
        return '📁';
      case WorktreeStatus.Error:
        return '❌';
      default:
        return '❓';
    }
  }

  /**
   * Get tooltip text
   */
  getTooltip(): string {
    let tooltip = `Path: ${this.path}\nBranch: ${this.branch}\nStatus: ${this.status}`;
    
    if (this.hasClaudeProcess && this.claudeProcessId) {
      tooltip += `\nClaude Process: ${this.claudeProcessId}`;
    }
    
    return tooltip;
  }

  /**
   * Convert to tree item
   */
  toTreeItem(): MonitorTreeItem {
    return {
      id: this.id,
      label: `${this.getStatusIcon()} ${this.getDisplayName()}`,
      description: this.branch,
      tooltip: this.getTooltip(),
      contextValue: 'worktree',
      children: this.hasClaudeProcess ? [
        {
          id: `${this.id}-claude`,
          label: `⚡ Claude: ${this.claudeProcessId}`,
          description: 'Running',
          tooltip: `Claude process running (PID: ${this.claudeProcessId})`,
          contextValue: 'claudeProcess'
        }
      ] : [
        {
          id: `${this.id}-no-claude`,
          label: '❌ No Claude process',
          description: 'Stopped',
          tooltip: 'No Claude process running in this worktree',
          contextValue: 'noClaudeProcess'
        }
      ]
    };
  }
}

export class ClaudeProcessModel implements ClaudeProcess {
  id: string;
  pid: number;
  command: string;
  workingDirectory: string;
  startTime: Date;
  status: ProcessStatus;
  associatedWorktree?: string;
  memoryUsage?: number;
  cpuUsage?: number;

  constructor(data: Partial<ClaudeProcess>) {
    this.id = data.id || this.generateId();
    this.pid = data.pid || 0;
    this.command = data.command || '';
    this.workingDirectory = data.workingDirectory || '';
    this.startTime = data.startTime || new Date();
    this.status = data.status || ProcessStatus.Unknown;
    this.associatedWorktree = data.associatedWorktree;
    this.memoryUsage = data.memoryUsage;
    this.cpuUsage = data.cpuUsage;
  }

  private generateId(): string {
    return `process-${this.pid}-${Date.now()}`;
  }

  /**
   * Update the process with new data
   */
  update(data: Partial<ClaudeProcess>): void {
    Object.assign(this, data);
  }

  /**
   * Get runtime duration
   */
  getRuntime(): string {
    return TimeUtils.getProcessRuntime(this.startTime);
  }

  /**
   * Get status icon
   */
  getStatusIcon(): string {
    switch (this.status) {
      case ProcessStatus.Running:
        return '🟢';
      case ProcessStatus.Stopped:
        return '🔴';
      case ProcessStatus.Error:
        return '❌';
      default:
        return '❓';
    }
  }

  /**
   * Get display command (shortened)
   */
  getDisplayCommand(): string {
    if (this.command.length > 30) {
      return this.command.substring(0, 27) + '...';
    }
    return this.command;
  }

  /**
   * Get memory usage display
   */
  getMemoryDisplay(): string {
    if (!this.memoryUsage) {return '';}
    
    const mb = this.memoryUsage / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  }

  /**
   * Get tooltip text
   */
  getTooltip(): string {
    let tooltip = `PID: ${this.pid}\nCommand: ${this.command}\nRuntime: ${this.getRuntime()}\nStatus: ${this.status}`;
    
    if (this.workingDirectory) {
      tooltip += `\nWorking Directory: ${this.workingDirectory}`;
    }
    
    if (this.associatedWorktree) {
      tooltip += `\nWorktree: ${this.associatedWorktree}`;
    }
    
    if (this.memoryUsage) {
      tooltip += `\nMemory: ${this.getMemoryDisplay()}`;
    }
    
    return tooltip;
  }

  /**
   * Convert to tree item
   */
  toTreeItem(): MonitorTreeItem {
    const children: MonitorTreeItem[] = [
      {
        id: `${this.id}-runtime`,
        label: `⏱️ Runtime: ${this.getRuntime()}`,
        description: '',
        tooltip: `Process started at ${this.startTime.toLocaleString()}`,
        contextValue: 'processInfo'
      }
    ];

    if (this.associatedWorktree) {
      children.push({
        id: `${this.id}-worktree`,
        label: `📁 Worktree: ${this.associatedWorktree}`,
        description: '',
        tooltip: `Associated with worktree: ${this.associatedWorktree}`,
        contextValue: 'processInfo'
      });
    }

    if (this.memoryUsage) {
      children.push({
        id: `${this.id}-memory`,
        label: `💾 Memory: ${this.getMemoryDisplay()}`,
        description: '',
        tooltip: `Memory usage: ${this.memoryUsage} bytes`,
        contextValue: 'processInfo'
      });
    }

    return {
      id: this.id,
      label: `${this.getStatusIcon()} ${this.getDisplayCommand()} (PID: ${this.pid})`,
      description: this.getRuntime(),
      tooltip: this.getTooltip(),
      contextValue: 'process',
      children
    };
  }
}

export class MonitorPanelStateModel implements MonitorPanelState {
  worktrees: Map<string, Worktree>;
  processes: Map<string, ClaudeProcess>;
  lastUpdate: Date;
  isRefreshing: boolean;

  constructor() {
    this.worktrees = new Map();
    this.processes = new Map();
    this.lastUpdate = new Date();
    this.isRefreshing = false;
  }

  /**
   * Update worktrees
   */
  updateWorktrees(worktrees: Worktree[]): void {
    this.worktrees.clear();
    
    for (const worktree of worktrees) {
      this.worktrees.set(worktree.id, new WorktreeModel(worktree));
    }
    
    this.lastUpdate = new Date();
  }

  /**
   * Update processes
   */
  updateProcesses(processes: ClaudeProcess[]): void {
    this.processes.clear();
    
    for (const process of processes) {
      this.processes.set(process.id, new ClaudeProcessModel(process));
    }
    
    this.lastUpdate = new Date();
  }

  /**
   * Associate processes with worktrees
   */
  associateProcessesWithWorktrees(): void {
    for (const [, worktree] of this.worktrees) {
      // Reset association
      worktree.hasClaudeProcess = false;
      worktree.claudeProcessId = undefined;
    }

    for (const [, process] of this.processes) {
      // Find matching worktree by working directory
      for (const [, worktree] of this.worktrees) {
        if (PathUtils.areSamePath(process.workingDirectory, worktree.path)) {
          worktree.hasClaudeProcess = true;
          worktree.claudeProcessId = process.pid;
          process.associatedWorktree = worktree.name;
          break;
        }
      }
    }
  }

  /**
   * Get statistics
   */
  getStats(): {
    totalWorktrees: number;
    activeWorktrees: number;
    totalProcesses: number;
    runningProcesses: number;
    lastUpdateTime: string;
  } {
    let activeWorktrees = 0;
    let runningProcesses = 0;

    for (const [, worktree] of this.worktrees) {
      if (worktree.status === WorktreeStatus.Active) {
        activeWorktrees++;
      }
    }

    for (const [, process] of this.processes) {
      if (process.status === ProcessStatus.Running) {
        runningProcesses++;
      }
    }

    return {
      totalWorktrees: this.worktrees.size,
      activeWorktrees,
      totalProcesses: this.processes.size,
      runningProcesses,
      lastUpdateTime: TimeUtils.formatTime(this.lastUpdate)
    };
  }

  /**
   * Clear all data
   */
  clear(): void {
    this.worktrees.clear();
    this.processes.clear();
    this.lastUpdate = new Date();
  }
}