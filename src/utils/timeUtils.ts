/**
 * Time and duration utilities for the Gadugi VS Code extension
 */
export class TimeUtils {
  /**
   * Format a duration in milliseconds to a human-readable string
   */
  static formatDuration(durationMs: number): string {
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    const remainingMinutes = minutes % 60;
    const remainingSeconds = seconds % 60;

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${remainingMinutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
      return `${remainingMinutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
  }

  /**
   * Calculate the duration between two dates in milliseconds
   */
  static calculateDuration(startTime: Date, endTime: Date = new Date()): number {
    return endTime.getTime() - startTime.getTime();
  }

  /**
   * Get the runtime duration for a process given its start time
   */
  static getProcessRuntime(startTime: Date): string {
    const duration = TimeUtils.calculateDuration(startTime);
    return TimeUtils.formatDuration(duration);
  }

  /**
   * Parse a date from various string formats commonly found in process information
   */
  static parseProcessStartTime(timeString: string): Date {
    // Try different common formats
    const formats = [
      // ISO 8601 format
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/,
      // Unix timestamp
      /^\d{10}$/,
      // Process start time format on Unix (e.g., "Jan 1 12:34")
      /^[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}/,
    ];

    // Try ISO format first
    if (formats[0].test(timeString)) {
      return new Date(timeString);
    }

    // Try Unix timestamp
    if (formats[1].test(timeString)) {
      return new Date(parseInt(timeString, 10) * 1000);
    }

    // For other formats, try to parse directly
    const parsed = new Date(timeString);
    if (!isNaN(parsed.getTime())) {
      return parsed;
    }

    // If all else fails, return current time minus a reasonable default
    console.warn(`Unable to parse process start time: ${timeString}`);
    return new Date(Date.now() - 60000); // Default to 1 minute ago
  }

  /**
   * Get a human-readable timestamp string
   */
  static getTimestamp(): string {
    return new Date().toLocaleTimeString();
  }

  /**
   * Get an ISO timestamp string
   */
  static getISOTimestamp(): string {
    return new Date().toISOString();
  }

  /**
   * Check if a date is within the last N minutes
   */
  static isWithinLastMinutes(date: Date, minutes: number): boolean {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    return diff <= minutes * 60 * 1000;
  }

  /**
   * Format a date to a short time string (HH:MM:SS)
   */
  static formatTime(date: Date): string {
    return date.toTimeString().split(' ')[0];
  }

  /**
   * Get a relative time string (e.g., "2 minutes ago")
   */
  static getRelativeTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (minutes > 0) {
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
      return `${seconds} second${seconds > 1 ? 's' : ''} ago`;
    }
  }

  /**
   * Debounce a function call
   */
  static debounce<T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout;

    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func(...args), delay);
    };
  }

  /**
   * Throttle a function call
   */
  static throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): (...args: Parameters<T>) => void {
    let inThrottle: boolean;

    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
}
