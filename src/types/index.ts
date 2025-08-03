/**
 * Type definitions for Gadugi VS Code Extension
 */

export interface Worktree {
  id: string;
  name: string;
  path: string;
  branch: string;
  isMain: boolean;
  hasClaudeProcess: boolean;
  claudeProcessId?: number;
  status: WorktreeStatus;
}

export enum WorktreeStatus {
  Active = 'active',
  Inactive = 'inactive',
  Error = 'error'
}

export interface ClaudeProcess {
  id: string;
  pid: number;
  command: string;
  workingDirectory: string;
  startTime: Date;
  status: ProcessStatus;
  associatedWorktree?: string;
  memoryUsage?: number;
  cpuUsage?: number;
}

export enum ProcessStatus {
  Running = 'running',
  Stopped = 'stopped',
  Error = 'error',
  Unknown = 'unknown'
}

export interface MonitorPanelState {
  worktrees: Map<string, Worktree>;
  processes: Map<string, ClaudeProcess>;
  lastUpdate: Date;
  isRefreshing: boolean;
}

export interface UpdateManagerConfig {
  interval: number;
  enabled: boolean;
}

export interface LaunchConfig {
  command: string;
  args: string[];
  workingDirectory: string;
  env?: Record<string, string>;
}

export interface ProcessInfo {
  pid: number;
  ppid: number;
  command: string;
  args: string[];
  workingDirectory: string;
  startTime: Date;
  memoryUsage?: number;
  cpuUsage?: number;
}

export interface WorktreeInfo {
  path: string;
  head: string;
  branch: string;
  bare: boolean;
  detached: boolean;
}

export interface MonitorTreeItem {
  id: string;
  label: string;
  description?: string;
  tooltip?: string;
  contextValue: string;
  iconPath?: string;
  collapsibleState?: number;
  children?: MonitorTreeItem[];
  command?: {
    command: string;
    title: string;
    arguments?: any[];
  };
}

export interface GitCommandResult {
  success: boolean;
  output: string;
  error?: string;
}

export interface ProcessCommandResult {
  success: boolean;
  processes: ProcessInfo[];
  error?: string;
}

export interface ExtensionConfig {
  updateInterval: number;
  claudeCommand: string;
  showResourceUsage: boolean;
}

export interface BloomCommandResult {
  success: boolean;
  terminalsCreated: number;
  claudeInstancesStarted: number;
  errors: string[];
}

export interface ErrorContext {
  operation: string;
  details: any;
  timestamp: Date;
}

export interface PerformanceMetrics {
  operationName: string;
  duration: number;
  timestamp: Date;
  success: boolean;
}