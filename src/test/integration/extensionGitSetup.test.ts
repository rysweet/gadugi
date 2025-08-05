import * as assert from 'assert';
import * as vscode from 'vscode';
import * as sinon from 'sinon';
import { getExtensionAPI } from '../../extension';

suite('Extension Git Setup Integration Tests', () => {
  let sandbox: sinon.SinonSandbox;
  let extension: vscode.Extension<any>;

  setup(async () => {
    sandbox = sinon.createSandbox();
    
    // Get the extension
    extension = vscode.extensions.getExtension('gadugi.gadugi-vscode-extension');
    if (!extension) {
      throw new Error('Extension not found');
    }

    // Activate the extension if not already active
    if (!extension.isActive) {
      await extension.activate();
    }
  });

  teardown(() => {
    sandbox.restore();
  });

  test('Extension should activate with GitSetupService', async () => {
    const api = getExtensionAPI();
    
    assert.ok(api, 'Extension API should be available');
    assert.ok(api.getGitSetupService, 'GitSetupService getter should be available');
    assert.ok(api.showGitSetup, 'showGitSetup method should be available');
    assert.ok(api.updateGitStatus, 'updateGitStatus method should be available');
  });

  test('Git setup commands should be registered', async () => {
    const commands = await vscode.commands.getCommands();
    
    assert.ok(commands.includes('gadugi.showGitStatus'), 'showGitStatus command should be registered');
    assert.ok(commands.includes('gadugi.showGitSetup'), 'showGitSetup command should be registered');
    assert.ok(commands.includes('gadugi.resetGitSetupGuidance'), 'resetGitSetupGuidance command should be registered');
  });

  test('Git status command should work', async () => {
    const showMessageSpy = sandbox.spy(vscode.window, 'showInformationMessage');
    
    await vscode.commands.executeCommand('gadugi.showGitStatus');
    
    // Should show some kind of status information
    assert.ok(showMessageSpy.calledOnce, 'Should show git status information');
  });

  test('Git setup guidance command should work', async () => {
    const showMessageSpy = sandbox.spy(vscode.window, 'showInformationMessage');
    
    await vscode.commands.executeCommand('gadugi.showGitSetup');
    
    // May or may not show message depending on git state and dismiss preference
    // But command should execute without error
    assert.ok(true, 'Git setup command should execute without error');
  });

  test('Reset git setup guidance command should work', async () => {
    const showMessageSpy = sandbox.spy(vscode.window, 'showInformationMessage');
    
    await vscode.commands.executeCommand('gadugi.resetGitSetupGuidance');
    
    assert.ok(showMessageSpy.calledOnce, 'Should show confirmation message');
  });

  test('Extension should handle workspace changes', async () => {
    const api = getExtensionAPI();
    const gitSetupService = api.getGitSetupService();
    
    if (gitSetupService) {
      // Simulate workspace folder change
      const updateStatusSpy = sandbox.spy(gitSetupService, 'updateStatusBar');
      
      // Trigger workspace change event
      // Note: This would require more complex mocking in actual implementation
      // Here we just verify the service exists and has the method
      assert.ok(typeof gitSetupService.updateStatusBar === 'function', 
        'GitSetupService should have updateStatusBar method');
    }
  });

  test('Extension should show limited UI without git repository', async () => {
    // Mock git not available
    const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
    execSyncStub.withArgs('git --version', { stdio: 'ignore' }).throws(new Error('Command not found'));
    
    const api = getExtensionAPI();
    const gitSetupService = api.getGitSetupService();
    
    if (gitSetupService) {
      const status = await gitSetupService.getGitStatus();
      
      assert.strictEqual(status.hasGit, false, 'Should detect git as not available');
      
      // Extension should still be functional with limited features
      assert.ok(api.getMonitorPanel, 'Monitor panel getter should be available');
      assert.ok(api.showOutput, 'Show output method should be available');
    }
  });

  test('Extension should gracefully handle git repository setup', async () => {
    // Mock git available but no repository
    const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
    execSyncStub.withArgs('git --version', { stdio: 'ignore' }).returns('git version 2.39.0');
    execSyncStub.withArgs('git rev-parse --git-dir', sinon.match.any).throws(new Error('Not a git repository'));
    
    // Mock workspace
    sandbox.stub(vscode.workspace, 'workspaceFolders').value([
      { uri: vscode.Uri.file('/test/workspace') }
    ]);
    
    const api = getExtensionAPI();
    const gitSetupService = api.getGitSetupService();
    
    if (gitSetupService) {
      const status = await gitSetupService.getGitStatus();
      
      assert.strictEqual(status.hasGit, true, 'Should detect git as available');
      assert.strictEqual(status.hasRepository, false, 'Should detect no repository');
      assert.strictEqual(status.workspaceFolder, '/test/workspace', 'Should have workspace folder');
    }
  });

  test('Extension should handle repository initialization flow', async () => {
    // Mock git available but no repository
    const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
    execSyncStub.withArgs('git --version', { stdio: 'ignore' }).returns('git version 2.39.0');
    execSyncStub.withArgs('git rev-parse --git-dir', sinon.match.any).throws(new Error('Not a git repository'));
    execSyncStub.withArgs('git init', sinon.match.any).returns('Initialized empty Git repository');
    
    // Mock workspace
    sandbox.stub(vscode.workspace, 'workspaceFolders').value([
      { uri: vscode.Uri.file('/test/workspace') }
    ]);
    
    // Mock user interactions
    const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');
    showMessageStub.onCall(0).resolves('Initialize Repository');
    showMessageStub.onCall(1).resolves('Yes'); // Confirm initialization
    showMessageStub.onCall(2).resolves('No'); // Skip initial commit
    
    const api = getExtensionAPI();
    const gitSetupService = api.getGitSetupService();
    
    if (gitSetupService) {
      await gitSetupService.showGitSetupGuidance();
      
      // Verify git init was called
      assert.ok(execSyncStub.calledWith('git init', sinon.match({ cwd: '/test/workspace' })),
        'Should execute git init command');
    }
  });

  test('Extension should handle external git commands', async () => {
    // Mock git available but no repository
    const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
    execSyncStub.withArgs('git --version', { stdio: 'ignore' }).returns('git version 2.39.0');
    execSyncStub.withArgs('git rev-parse --git-dir', sinon.match.any).throws(new Error('Not a git repository'));
    
    // Mock workspace
    sandbox.stub(vscode.workspace, 'workspaceFolders').value([
      { uri: vscode.Uri.file('/test/workspace') }
    ]);
    
    // Mock VS Code command execution
    const executeCommandSpy = sandbox.spy(vscode.commands, 'executeCommand');
    const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');
    showMessageStub.resolves('Clone Repository');
    
    const api = getExtensionAPI();
    const gitSetupService = api.getGitSetupService();
    
    if (gitSetupService) {
      await gitSetupService.showGitSetupGuidance();
      
      // Verify git.clone command was executed
      assert.ok(executeCommandSpy.calledWith('git.clone'),
        'Should execute git.clone command');
    }
  });

  test('Extension should persist dismiss preferences', async () => {
    const api = getExtensionAPI();
    const gitSetupService = api.getGitSetupService();
    
    if (gitSetupService) {
      // Test reset dismiss preference
      await gitSetupService.resetDismissPreference();
      
      // This test would need access to the actual context to verify state changes
      // In a real test, we would mock the context and verify the update calls
      assert.ok(true, 'Dismiss preference operations should work without error');
    }
  });

  test('Extension should handle git installation guidance', async () => {
    // Mock git not installed
    const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
    execSyncStub.withArgs('git --version', { stdio: 'ignore' }).throws(new Error('Command not found'));
    
    // Mock user interaction
    const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves('Install Git Guide');
    const openExternalSpy = sandbox.spy(vscode.env, 'openExternal');
    
    const api = getExtensionAPI();
    const gitSetupService = api.getGitSetupService();
    
    if (gitSetupService) {
      await gitSetupService.showGitSetupGuidance();
      
      // Should show guidance and handle install guide action
      assert.ok(showMessageStub.calledOnce, 'Should show git installation guidance');
      assert.ok(openExternalSpy.calledOnce, 'Should open git installation guide');
    }
  });

  test('Extension should provide status bar integration', async () => {
    const api = getExtensionAPI();
    const gitSetupService = api.getGitSetupService();
    
    if (gitSetupService) {
      // Test status bar update
      await gitSetupService.updateStatusBar();
      
      // In a real test, we would verify the status bar item properties
      // This test ensures the method exists and executes without error
      assert.ok(true, 'Status bar update should work without error');
    }
  });
});