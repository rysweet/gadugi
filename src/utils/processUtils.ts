import { exec, spawn } from 'child_process';
import * as os from 'os';
import { ProcessInfo, ProcessCommandResult } from '../types';
import { TimeUtils } from './timeUtils';
import { ErrorUtils } from './errorUtils';

/**
 * Cross-platform process utilities for the Gadugi VS Code extension
 */
export class ProcessUtils {
  /**
   * Get all running processes on the system
   */
  static async getAllProcesses(): Promise<ProcessCommandResult> {
    try {
      const platform = os.platform();
      let command: string;
      let parser: (output: string) => ProcessInfo[];

      switch (platform) {
        case 'win32':
          command = 'tasklist /fo csv /v';
          parser = ProcessUtils.parseWindowsProcesses;
          break;
        case 'darwin':
          command = 'ps -eo pid,ppid,lstart,command';
          parser = ProcessUtils.parseMacOSProcesses;
          break;
        case 'linux':
          command = 'ps -eo pid,ppid,lstart,command';
          parser = ProcessUtils.parseLinuxProcesses;
          break;
        default:
          throw new Error(`Unsupported platform: ${platform}`);
      }

      return new Promise((resolve) => {
        exec(command, (error, stdout, stderr) => {
          if (error) {
            ErrorUtils.logError(error, ErrorUtils.createErrorContext('process-discovery', { command, stderr }));
            resolve({ success: false, processes: [], error: error.message });
            return;
          }

          try {
            const processes = parser(stdout);
            resolve({ success: true, processes });
          } catch (parseError) {
            const err = parseError instanceof Error ? parseError : new Error(String(parseError));
            ErrorUtils.logError(err, ErrorUtils.createErrorContext('process-parsing', { stdout }));
            resolve({ success: false, processes: [], error: err.message });
          }
        });
      });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('process-discovery-setup'));
      return { success: false, processes: [], error: err.message };
    }
  }

  /**
   * Get Claude Code processes specifically
   */
  static async getClaudeProcesses(): Promise<ProcessInfo[]> {
    const result = await ProcessUtils.getAllProcesses();
    if (!result.success) {
      return [];
    }

    return result.processes.filter(process =>
      ProcessUtils.isClaudeProcess(process.command)
    );
  }

  /**
   * Check if a command string represents a Claude Code process
   */
  private static isClaudeProcess(command: string): boolean {
    const claudeIndicators = [
      'claude',
      'Claude',
      'CLAUDE'
    ];

    const lowerCommand = command.toLowerCase();
    return claudeIndicators.some(indicator =>
      lowerCommand.includes(indicator.toLowerCase()) &&
      (lowerCommand.includes('--resume') || lowerCommand.includes('code'))
    );
  }

  /**
   * Parse Windows process list output
   */
  private static parseWindowsProcesses(output: string): ProcessInfo[] {
    const lines = output.split('\n').slice(1); // Skip header
    const processes: ProcessInfo[] = [];

    for (const line of lines) {
      if (!line.trim()) {continue;}

      try {
        // Parse CSV output from tasklist
        const columns = ProcessUtils.parseCSVLine(line);
        if (columns.length < 5) {continue;}

        const [imageName, pid, , , memUsage] = columns;

        processes.push({
          pid: parseInt(pid.replace(/"/g, ''), 10),
          ppid: 0, // Not easily available from tasklist
          command: imageName.replace(/"/g, ''),
          args: [],
          workingDirectory: '',
          startTime: new Date(), // Not easily available from tasklist
          memoryUsage: ProcessUtils.parseMemoryUsage(memUsage?.replace(/"/g, '') || ''),
        });
      } catch (error) {
        // Skip malformed lines
        continue;
      }
    }

    return processes;
  }

  /**
   * Parse macOS process list output
   */
  private static parseMacOSProcesses(output: string): ProcessInfo[] {
    const lines = output.split('\n').slice(1); // Skip header
    const processes: ProcessInfo[] = [];

    for (const line of lines) {
      if (!line.trim()) {continue;}

      try {
        // Parse ps output: PID PPID STARTED COMMAND
        const match = line.match(/^\s*(\d+)\s+(\d+)\s+(.+?)\s+(.+)$/);
        if (!match) {continue;}

        const [, pidStr, ppidStr, startTimeStr, command] = match;
        const pid = parseInt(pidStr, 10);
        const ppid = parseInt(ppidStr, 10);

        processes.push({
          pid,
          ppid,
          command,
          args: ProcessUtils.parseCommandArgs(command),
          workingDirectory: '',
          startTime: TimeUtils.parseProcessStartTime(startTimeStr),
        });
      } catch (error) {
        // Skip malformed lines
        continue;
      }
    }

    return processes;
  }

  /**
   * Parse Linux process list output (similar to macOS)
   */
  private static parseLinuxProcesses(output: string): ProcessInfo[] {
    return ProcessUtils.parseMacOSProcesses(output); // Same format
  }

  /**
   * Parse CSV line accounting for quoted values
   */
  private static parseCSVLine(line: string): string[] {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];

      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current);
        current = '';
      } else {
        current += char;
      }
    }

    result.push(current);
    return result;
  }

  /**
   * Parse memory usage string (e.g., "1,234 K" -> 1234000)
   */
  private static parseMemoryUsage(memStr: string): number | undefined {
    if (!memStr) {return undefined;}

    const match = memStr.match(/([0-9,]+)\s*([KMG]?)/i);
    if (!match) {return undefined;}

    const [, numStr, unit] = match;
    const num = parseInt(numStr.replace(/,/g, ''), 10);

    switch (unit.toUpperCase()) {
      case 'K': return num * 1024;
      case 'M': return num * 1024 * 1024;
      case 'G': return num * 1024 * 1024 * 1024;
      default: return num;
    }
  }

  /**
   * Parse command string into command and args
   */
  private static parseCommandArgs(command: string): string[] {
    // Simple space-based splitting (could be enhanced for quoted args)
    return command.split(/\s+/).filter(arg => arg.length > 0);
  }

  /**
   * Get the working directory of a process
   */
  static async getProcessWorkingDirectory(pid: number): Promise<string> {
    try {
      const platform = os.platform();
      let command: string;

      switch (platform) {
        case 'win32':
          // Windows doesn't have an easy way to get cwd from PID
          return '';
        case 'darwin':
          command = `lsof -p ${pid} | grep cwd | awk '{print $9}'`;
          break;
        case 'linux':
          command = `readlink -f /proc/${pid}/cwd`;
          break;
        default:
          return '';
      }

      return new Promise((resolve) => {
        exec(command, (error, stdout) => {
          if (error) {
            resolve('');
            return;
          }
          resolve(stdout.trim());
        });
      });
    } catch {
      return '';
    }
  }

  /**
   * Kill a process by PID
   */
  static async killProcess(pid: number): Promise<boolean> {
    try {
      const platform = os.platform();
      let command: string;

      switch (platform) {
        case 'win32':
          command = `taskkill /PID ${pid} /F`;
          break;
        default:
          command = `kill ${pid}`;
          break;
      }

      return new Promise((resolve) => {
        exec(command, (error) => {
          resolve(!error);
        });
      });
    } catch {
      return false;
    }
  }

  /**
   * Start a new process
   */
  static async startProcess(
    command: string,
    args: string[],
    workingDirectory?: string
  ): Promise<{ success: boolean; pid?: number; error?: string }> {
    try {
      const childProcess = spawn(command, args, {
        cwd: workingDirectory,
        detached: true,
        stdio: 'ignore'
      });

      return new Promise((resolve) => {
        childProcess.on('spawn', () => {
          resolve({ success: true, pid: childProcess.pid });
        });

        childProcess.on('error', (error) => {
          resolve({ success: false, error: error.message });
        });
      });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      return { success: false, error: err.message };
    }
  }

  /**
   * Check if a process is still running
   */
  static async isProcessRunning(pid: number): Promise<boolean> {
    try {
      const platform = os.platform();

      if (platform === 'win32') {
        return new Promise((resolve) => {
          exec(`tasklist /fi "PID eq ${pid}"`, (error, stdout) => {
            resolve(!error && stdout.includes(pid.toString()));
          });
        });
      } else {
        return new Promise((resolve) => {
          exec(`ps -p ${pid}`, (error) => {
            resolve(!error);
          });
        });
      }
    } catch {
      return false;
    }
  }
}
