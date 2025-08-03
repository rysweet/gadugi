import * as path from 'path';
import * as os from 'os';

/**
 * Cross-platform path utilities for the Gadugi VS Code extension
 */
export class PathUtils {
  /**
   * Normalize a file path for the current platform
   */
  static normalize(filePath: string): string {
    return path.normalize(filePath);
  }

  /**
   * Get the relative path from one directory to another
   */
  static getRelativePath(from: string, to: string): string {
    return path.relative(from, to);
  }

  /**
   * Get the basename of a path (directory or file name)
   */
  static getBasename(filePath: string): string {
    return path.basename(filePath);
  }

  /**
   * Get the directory name of a path
   */
  static getDirname(filePath: string): string {
    return path.dirname(filePath);
  }

  /**
   * Join multiple path segments
   */
  static join(...segments: string[]): string {
    return path.join(...segments);
  }

  /**
   * Check if a path is absolute
   */
  static isAbsolute(filePath: string): boolean {
    return path.isAbsolute(filePath);
  }

  /**
   * Resolve a path to an absolute path
   */
  static resolve(...segments: string[]): string {
    return path.resolve(...segments);
  }

  /**
   * Get the home directory path
   */
  static getHomeDirectory(): string {
    return os.homedir();
  }

  /**
   * Get the platform-specific path separator
   */
  static getPathSeparator(): string {
    return path.sep;
  }

  /**
   * Convert a Windows path to Unix-style path (for display purposes)
   */
  static toUnixStyle(filePath: string): string {
    return filePath.replace(/\\/g, '/');
  }

  /**
   * Get a display-friendly version of a path (shortened if needed)
   */
  static getDisplayPath(filePath: string, maxLength: number = 50): string {
    if (filePath.length <= maxLength) {
      return filePath;
    }

    const homeDir = PathUtils.getHomeDirectory();
    if (filePath.startsWith(homeDir)) {
      const relativePath = '~' + filePath.substring(homeDir.length);
      if (relativePath.length <= maxLength) {
        return relativePath;
      }
    }

    // Truncate from the beginning, keeping the end
    const truncated = '...' + filePath.substring(filePath.length - maxLength + 3);
    return truncated;
  }

  /**
   * Check if two paths refer to the same location
   */
  static areSamePath(path1: string, path2: string): boolean {
    const normalized1 = PathUtils.normalize(PathUtils.resolve(path1));
    const normalized2 = PathUtils.normalize(PathUtils.resolve(path2));
    
    // Case-insensitive comparison on Windows
    if (os.platform() === 'win32') {
      return normalized1.toLowerCase() === normalized2.toLowerCase();
    }
    
    return normalized1 === normalized2;
  }

  /**
   * Get the worktree name from a path (for display purposes)
   */
  static getWorktreeName(worktreePath: string): string {
    const basename = PathUtils.getBasename(worktreePath);
    
    // If it's in a .worktrees directory, use the basename
    if (worktreePath.includes('.worktrees')) {
      return basename;
    }
    
    // If it's the main worktree, use 'main' or the directory name
    return basename || 'main';
  }

  /**
   * Check if a path exists in a worktrees subdirectory
   */
  static isWorktreeSubdirectory(worktreePath: string): boolean {
    return worktreePath.includes('.worktrees') || worktreePath.includes('worktrees');
  }

  /**
   * Sanitize a path for use in terminal names or identifiers
   */
  static sanitizeForIdentifier(filePath: string): string {
    return PathUtils.getBasename(filePath)
      .replace(/[^a-zA-Z0-9\-_]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }
}