import * as vscode from 'vscode';
import { UpdateManagerConfig } from '../types';
import { ErrorUtils } from '../utils/errorUtils';
import { TimeUtils } from '../utils/timeUtils';

/**
 * Manages real-time updates for the monitor panel
 */
export class UpdateManager {
  private config: UpdateManagerConfig;
  private updateInterval?: NodeJS.Timeout;
  private subscribers: Set<() => Promise<void>> = new Set();
  private isUpdating: boolean = false;
  private lastUpdateTime: Date = new Date();

  constructor(config: Partial<UpdateManagerConfig> = {}) {
    this.config = {
      interval: config.interval || 3000, // Default 3 seconds
      enabled: config.enabled ?? true
    };
  }

  /**
   * Start the update manager
   */
  start(): void {
    if (this.updateInterval) {
      this.stop(); // Stop existing interval
    }

    if (!this.config.enabled) {
      ErrorUtils.logInfo('Update manager is disabled', 'update-manager');
      return;
    }

    ErrorUtils.logInfo(`Starting update manager with ${this.config.interval}ms interval`, 'update-manager');

    this.updateInterval = setInterval(async () => {
      await this.performUpdate();
    }, this.config.interval);

    // Perform initial update
    this.performUpdate();
  }

  /**
   * Stop the update manager
   */
  stop(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = undefined;
      ErrorUtils.logInfo('Update manager stopped', 'update-manager');
    }
  }

  /**
   * Subscribe to updates
   */
  subscribe(callback: () => Promise<void>): () => void {
    this.subscribers.add(callback);
    
    return () => {
      this.subscribers.delete(callback);
    };
  }

  /**
   * Unsubscribe from updates
   */
  unsubscribe(callback: () => Promise<void>): void {
    this.subscribers.delete(callback);
  }

  /**
   * Perform an update cycle
   */
  private async performUpdate(): Promise<void> {
    if (this.isUpdating) {
      return; // Skip if already updating
    }

    this.isUpdating = true;
    const startTime = Date.now();

    try {
      // Notify all subscribers
      const updatePromises = Array.from(this.subscribers).map(async (callback) => {
        try {
          await callback();
        } catch (error) {
          const err = error instanceof Error ? error : new Error(String(error));
          ErrorUtils.logError(err, ErrorUtils.createErrorContext('update-manager-callback'));
        }
      });

      await Promise.all(updatePromises);
      
      this.lastUpdateTime = new Date();
      const duration = Date.now() - startTime;
      
      if (duration > 1000) {
        ErrorUtils.logWarning(`Slow update cycle: ${duration}ms`, 'update-manager');
      }

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      ErrorUtils.logError(err, ErrorUtils.createErrorContext('update-manager-cycle'));
    } finally {
      this.isUpdating = false;
    }
  }

  /**
   * Force an immediate update
   */
  async forceUpdate(): Promise<void> {
    await this.performUpdate();
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<UpdateManagerConfig>): void {
    const oldInterval = this.config.interval;
    const wasEnabled = this.config.enabled;

    this.config = { ...this.config, ...config };

    // Restart if interval changed or enabled state changed
    if (this.config.interval !== oldInterval || this.config.enabled !== wasEnabled) {
      if (this.updateInterval) {
        this.stop();
        this.start();
      }
    }

    ErrorUtils.logInfo(`Update manager configuration updated: interval=${this.config.interval}ms, enabled=${this.config.enabled}`, 'update-manager');
  }

  /**
   * Get current configuration
   */
  getConfig(): UpdateManagerConfig {
    return { ...this.config };
  }

  /**
   * Get update statistics
   */
  getStats(): {
    isRunning: boolean;
    isUpdating: boolean;
    subscriberCount: number;
    lastUpdateTime: string;
    interval: number;
  } {
    return {
      isRunning: !!this.updateInterval,
      isUpdating: this.isUpdating,
      subscriberCount: this.subscribers.size,
      lastUpdateTime: TimeUtils.formatTime(this.lastUpdateTime),
      interval: this.config.interval
    };
  }

  /**
   * Create a throttled version of a callback
   */
  static createThrottledCallback(
    callback: () => Promise<void>,
    interval: number
  ): () => Promise<void> {
    let lastCall = 0;
    let pending = false;

    return async () => {
      const now = Date.now();
      
      if (now - lastCall >= interval && !pending) {
        lastCall = now;
        pending = true;
        
        try {
          await callback();
        } finally {
          pending = false;
        }
      }
    };
  }

  /**
   * Create a debounced version of a callback
   */
  static createDebouncedCallback(
    callback: () => Promise<void>,
    delay: number
  ): () => void {
    let timeoutId: NodeJS.Timeout;
    
    return () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(async () => {
        try {
          await callback();
        } catch (error) {
          const err = error instanceof Error ? error : new Error(String(error));
          ErrorUtils.logError(err, ErrorUtils.createErrorContext('debounced-callback'));
        }
      }, delay);
    };
  }

  /**
   * Setup configuration from VS Code settings
   */
  setupFromConfiguration(): void {
    const config = vscode.workspace.getConfiguration('gadugi');
    const interval = config.get<number>('updateInterval', 3000);
    
    this.updateConfig({
      interval,
      enabled: true
    });

    // Listen for configuration changes
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (event.affectsConfiguration('gadugi.updateInterval')) {
        const newInterval = vscode.workspace.getConfiguration('gadugi').get<number>('updateInterval', 3000);
        this.updateConfig({ interval: newInterval });
      }
    });
  }

  /**
   * Cleanup resources
   */
  dispose(): void {
    this.stop();
    this.subscribers.clear();
  }

  /**
   * Pause updates temporarily
   */
  pause(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = undefined;
    }
  }

  /**
   * Resume updates
   */
  resume(): void {
    if (!this.updateInterval && this.config.enabled) {
      this.start();
    }
  }

  /**
   * Check if updates are active
   */
  isActive(): boolean {
    return !!this.updateInterval && this.config.enabled;
  }

  /**
   * Add performance monitoring
   */
  enablePerformanceMonitoring(): void {
    const originalPerformUpdate = this.performUpdate.bind(this);
    
    this.performUpdate = async () => {
      const startTime = Date.now();
      
      try {
        await originalPerformUpdate();
      } finally {
        const duration = Date.now() - startTime;
        
        if (duration > 2000) {
          ErrorUtils.logWarning(`Very slow update cycle: ${duration}ms`, 'update-manager-performance');
        }
      }
    };
  }

  /**
   * Set update interval from VS Code configuration
   */
  static getIntervalFromConfig(): number {
    const config = vscode.workspace.getConfiguration('gadugi');
    return config.get<number>('updateInterval', 3000);
  }

  /**
   * Create update manager from VS Code configuration
   */
  static fromConfiguration(): UpdateManager {
    const interval = UpdateManager.getIntervalFromConfig();
    
    const manager = new UpdateManager({
      interval,
      enabled: true
    });

    manager.setupFromConfiguration();
    return manager;
  }
}