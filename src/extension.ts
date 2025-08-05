import * as vscode from 'vscode';
import { BloomCommand } from './commands/bloomCommand';
import { MonitorPanel } from './panels/monitorPanel';
import { TerminalService } from './services/terminalService';
import { GitSetupService } from './services/gitSetupService';
import { ErrorUtils } from './utils/errorUtils';

/**
 * Main extension entry point for the Gadugi VS Code extension
 */

let monitorPanel: MonitorPanel | undefined;
let terminalService: TerminalService | undefined;
let gitSetupService: GitSetupService | undefined;

/**
 * Extension activation function
 */
export async function activate(context: vscode.ExtensionContext) {
  try {
    ErrorUtils.logInfo('Gadugi VS Code extension is activating...', 'extension-activation');

    // Initialize Git setup service first (needed for all validations)
    gitSetupService = new GitSetupService(context);
    
    // Validate prerequisites
    const validation = await validateExtensionPrerequisites();
    if (validation.issues.length > 0) {
      ErrorUtils.logWarning(`Extension prerequisites not fully met: ${validation.issues.join(', ')}`, 'extension-activation');
      
      // Show git setup guidance for git-related issues instead of generic error
      const hasGitIssues = validation.issues.some(issue => 
        issue.includes('Git') || issue.includes('git repository')
      );
      
      if (hasGitIssues && gitSetupService) {
        // Show helpful guidance instead of error message
        await gitSetupService.showGitSetupGuidance();
      }
      
      // Only prevent activation for critical non-git issues
      if (!validation.canContinue && !hasGitIssues) {
        await ErrorUtils.showErrorMessage(
          `Gadugi extension cannot start: ${validation.issues.join(', ')}`,
          'Show Details'
        );
        return;
      }
    }

    // Initialize services
    terminalService = new TerminalService();

    // Setup terminal event listeners
    const terminalDisposables = terminalService.setupEventListeners();
    context.subscriptions.push(...terminalDisposables);

    // Register the Bloom command
    const bloomCommandDisposable = BloomCommand.register(context);
    context.subscriptions.push(bloomCommandDisposable);

    // Create and register the monitor panel
    monitorPanel = MonitorPanel.create(context);

    // Register additional commands
    registerAdditionalCommands(context);

    // Setup extension-level event listeners
    setupExtensionEventListeners(context);

    // Show activation success
    ErrorUtils.logInfo('Gadugi VS Code extension activated successfully', 'extension-activation');

    // Show welcome message on first activation
    await showWelcomeMessage(context);

  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error));
    ErrorUtils.logError(err, ErrorUtils.createErrorContext('extension-activation'));

    await ErrorUtils.showErrorMessage(
      'Failed to activate Gadugi extension. Check the output for details.',
      'Show Output'
    );
  }
}

/**
 * Extension deactivation function
 */
export function deactivate() {
  try {
    ErrorUtils.logInfo('Gadugi VS Code extension is deactivating...', 'extension-deactivation');

    // Cleanup monitor panel
    if (monitorPanel) {
      monitorPanel.dispose();
      monitorPanel = undefined;
    }

    // Cleanup terminal service
    if (terminalService) {
      // Terminal service cleanup is handled by VS Code automatically
      terminalService = undefined;
    }

    // Cleanup git setup service
    if (gitSetupService) {
      gitSetupService.dispose();
      gitSetupService = undefined;
    }

    ErrorUtils.logInfo('Gadugi VS Code extension deactivated', 'extension-deactivation');
  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error));
    ErrorUtils.logError(err, ErrorUtils.createErrorContext('extension-deactivation'));
  }
}

/**
 * Validate extension prerequisites
 */
async function validateExtensionPrerequisites(): Promise<{
  canContinue: boolean;
  issues: string[]
}> {
  const issues: string[] = [];

  try {
    // Check VS Code version
    const vscodeVersion = vscode.version;
    ErrorUtils.logInfo(`VS Code version: ${vscodeVersion}`, 'extension-validation');

    // Check workspace
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
      issues.push('No workspace folder is open');
    }

    // Check git availability
    const dependencyIssues = await ErrorUtils.validateDependencies();
    issues.push(...dependencyIssues);

    // Determine if extension can continue with warnings
    const criticalIssues = issues.filter(issue =>
      issue.includes('No workspace folder') ||
      issue.includes('Git is not installed')
    );

    return {
      canContinue: criticalIssues.length === 0,
      issues
    };

  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error));
    ErrorUtils.logError(err, ErrorUtils.createErrorContext('extension-prerequisite-validation'));
    return {
      canContinue: false,
      issues: [...issues, 'Failed to validate prerequisites']
    };
  }
}

/**
 * Register additional extension commands
 */
function registerAdditionalCommands(context: vscode.ExtensionContext): void {
  // Show output command
  context.subscriptions.push(
    vscode.commands.registerCommand('gadugi.showOutput', () => {
      ErrorUtils.showOutput();
    })
  );

  // Show extension info command
  context.subscriptions.push(
    vscode.commands.registerCommand('gadugi.showInfo', async () => {
      await showExtensionInfo();
    })
  );

  // Validate setup command
  context.subscriptions.push(
    vscode.commands.registerCommand('gadugi.validateSetup', async () => {
      await validateAndShowSetup();
    })
  );

  // Quick launch command (combines Bloom + show monitor)
  context.subscriptions.push(
    vscode.commands.registerCommand('gadugi.quickStart', async () => {
      await executeQuickStart();
    })
  );

  // Git setup commands
  context.subscriptions.push(
    vscode.commands.registerCommand('gadugi.showGitStatus', async () => {
      if (gitSetupService) {
        await gitSetupService.showGitStatusDetails();
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('gadugi.showGitSetup', async () => {
      if (gitSetupService) {
        await gitSetupService.showGitSetupGuidance();
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('gadugi.resetGitSetupGuidance', async () => {
      if (gitSetupService) {
        await gitSetupService.resetDismissPreference();
      }
    })
  );

  ErrorUtils.logInfo('Additional commands registered', 'extension-commands');
}

/**
 * Setup extension-level event listeners
 */
function setupExtensionEventListeners(context: vscode.ExtensionContext): void {
  // Listen for workspace changes
  context.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders(async () => {
      ErrorUtils.logInfo('Workspace folders changed', 'extension-events');

      if (monitorPanel) {
        await monitorPanel.refresh();
      }
      
      // Update git status when workspace changes
      if (gitSetupService) {
        await gitSetupService.updateStatusBar();
      }
    })
  );

  // Listen for configuration changes
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (event.affectsConfiguration('gadugi')) {
        ErrorUtils.logInfo('Gadugi configuration changed', 'extension-events');

        if (monitorPanel) {
          monitorPanel.refresh();
        }
      }
    })
  );

  // Listen for window state changes
  context.subscriptions.push(
    vscode.window.onDidChangeWindowState((windowState) => {
      if (windowState.focused) {
        ErrorUtils.logInfo('VS Code window focused', 'extension-events');

        // Refresh monitor panel when window regains focus
        if (monitorPanel && monitorPanel.isVisible()) {
          monitorPanel.refresh();
        }
      }
    })
  );

  ErrorUtils.logInfo('Extension event listeners setup', 'extension-events');
}

/**
 * Show welcome message on first activation
 */
async function showWelcomeMessage(context: vscode.ExtensionContext): Promise<void> {
  const hasShownWelcome = context.globalState.get<boolean>('gadugi.hasShownWelcome', false);

  if (!hasShownWelcome) {
    const message = 'Welcome to Gadugi! This extension helps manage git worktrees and Claude Code instances for parallel development.';
    const action = await vscode.window.showInformationMessage(
      message,
      'Show Monitor Panel',
      'Run Bloom Command',
      'Learn More',
      'Dismiss'
    );

    switch (action) {
      case 'Show Monitor Panel':
        if (monitorPanel) {
          monitorPanel.show();
        }
        break;
      case 'Run Bloom Command':
        await vscode.commands.executeCommand('gadugi.bloom');
        break;
      case 'Learn More':
        await vscode.env.openExternal(vscode.Uri.parse('https://github.com/gadugi/gadugi-vscode-extension'));
        break;
    }

    await context.globalState.update('gadugi.hasShownWelcome', true);
  }
}

/**
 * Show extension information
 */
async function showExtensionInfo(): Promise<void> {
  const extension = vscode.extensions.getExtension('gadugi.gadugi-vscode-extension');
  if (!extension) {
    await ErrorUtils.showErrorMessage('Extension information not available');
    return;
  }

  const info = `
Gadugi VS Code Extension
Version: ${extension.packageJSON.version}
Description: ${extension.packageJSON.description}

Features:
• Bloom Command: Auto-create terminals for all worktrees and start Claude Code
• Monitor Panel: Real-time monitoring of worktrees and Claude processes
• Terminal Management: Streamlined terminal creation and management
• Process Monitoring: Track Claude Code instances across worktrees

Commands:
• Gadugi: Bloom - Start Claude in all worktrees
• Gadugi: Refresh - Refresh monitor panel
• Gadugi: Show Output - Show extension logs
  `;

  await vscode.window.showInformationMessage(info, { modal: true }, 'OK');
}

/**
 * Validate and show setup status
 */
async function validateAndShowSetup(): Promise<void> {
  try {
    const validation = await validateExtensionPrerequisites();
    const dependencyIssues = await ErrorUtils.validateDependencies();

    let message = 'Gadugi Extension Setup Validation\\n\\n';

    if (validation.canContinue && dependencyIssues.length === 0) {
      message += '✅ All prerequisites met!\\n\\n';
      message += '• Workspace folder is open\\n';
      message += '• Git is available\\n';
      message += '• Extension is ready to use';
    } else {
      message += '⚠️  Some issues found:\\n\\n';

      const allIssues = [...validation.issues, ...dependencyIssues];
      for (const issue of allIssues) {
        message += `• ${issue}\\n`;
      }

      message += '\\nSome features may not work correctly.';
    }

    const action = await vscode.window.showInformationMessage(
      message,
      { modal: true },
      'Show Output',
      'OK'
    );

    if (action === 'Show Output') {
      ErrorUtils.showOutput();
    }

  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error));
    ErrorUtils.logError(err, ErrorUtils.createErrorContext('extension-setup-validation'));
    await ErrorUtils.showErrorMessage('Failed to validate setup');
  }
}

/**
 * Execute quick start workflow
 */
async function executeQuickStart(): Promise<void> {
  try {
    const action = await vscode.window.showInformationMessage(
      'Quick Start will run the Bloom command to create terminals and show the monitor panel. Continue?',
      'Yes',
      'No'
    );

    if (action !== 'Yes') {
      return;
    }

    // Execute Bloom command
    await vscode.commands.executeCommand('gadugi.bloom');

    // Show monitor panel
    if (monitorPanel) {
      monitorPanel.show();
    }

    await ErrorUtils.showInfoMessage('Quick start completed! Check the monitor panel for status.');

  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error));
    ErrorUtils.logError(err, ErrorUtils.createErrorContext('extension-quick-start'));
    await ErrorUtils.showErrorMessage('Quick start failed');
  }
}

/**
 * Get extension API for other extensions
 */
export function getExtensionAPI() {
  return {
    getMonitorPanel: () => monitorPanel,
    getTerminalService: () => terminalService,
    getGitSetupService: () => gitSetupService,
    executeBloom: () => vscode.commands.executeCommand('gadugi.bloom'),
    refreshMonitor: () => monitorPanel?.refresh(),
    showOutput: () => ErrorUtils.showOutput(),
    showGitSetup: () => gitSetupService?.showGitSetupGuidance(),
    updateGitStatus: () => gitSetupService?.updateStatusBar()
  };
}

/**
 * Extension metadata
 */
export const extensionMetadata = {
  name: 'Gadugi VS Code Extension',
  version: '0.1.0',
  description: 'Multi-agent development workflow management with git worktree and Claude Code integration',
  features: [
    'Bloom Command - Auto-setup Claude in all worktrees',
    'Monitor Panel - Real-time process and worktree monitoring',
    'Terminal Management - Streamlined terminal creation',
    'Process Monitoring - Track Claude Code instances'
  ]
};
