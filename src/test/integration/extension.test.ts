import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Extension Integration Test Suite', () => {
  vscode.window.showInformationMessage('Start all tests.');

  test('Extension should be present', () => {
    const extension = vscode.extensions.getExtension('gadugi.gadugi-vscode-extension');
    assert.ok(extension);
  });

  test('Extension should activate', async () => {
    const extension = vscode.extensions.getExtension('gadugi.gadugi-vscode-extension');
    assert.ok(extension);
    
    if (!extension.isActive) {
      await extension.activate();
    }
    
    assert.ok(extension.isActive);
  });

  test('Bloom command should be registered', async () => {
    const commands = await vscode.commands.getCommands(true);
    assert.ok(commands.includes('gadugi.bloom'));
  });

  test('Refresh command should be registered', async () => {
    const commands = await vscode.commands.getCommands(true);
    assert.ok(commands.includes('gadugi.refresh'));
  });

  test('Monitor tree view should be available', () => {
    // Check if the tree view is registered by looking for the view in the package.json contribution
    const extension = vscode.extensions.getExtension('gadugi.gadugi-vscode-extension');
    assert.ok(extension);
    
    const packageJson = extension.packageJSON;
    const views = packageJson.contributes?.views?.gadugi;
    assert.ok(views);
    
    const monitorView = views.find((view: any) => view.id === 'gadugi.monitor');
    assert.ok(monitorView);
    assert.strictEqual(monitorView.name, 'Worktree & Process Monitor');
  });

  test('Configuration should be available', () => {
    const config = vscode.workspace.getConfiguration('gadugi');
    assert.ok(config);
    
    // Test default values
    const updateInterval = config.get('updateInterval');
    const claudeCommand = config.get('claudeCommand');
    const showResourceUsage = config.get('showResourceUsage');
    
    assert.strictEqual(updateInterval, 3000);
    assert.strictEqual(claudeCommand, 'claude --resume');
    assert.strictEqual(showResourceUsage, true);
  });

  test('Commands should have proper titles', () => {
    const extension = vscode.extensions.getExtension('gadugi.gadugi-vscode-extension');
    assert.ok(extension);
    
    const packageJson = extension.packageJSON;
    const commands = packageJson.contributes?.commands;
    assert.ok(commands);
    
    const bloomCommand = commands.find((cmd: any) => cmd.command === 'gadugi.bloom');
    assert.ok(bloomCommand);
    assert.ok(bloomCommand.title.includes('Bloom'));
    assert.ok(bloomCommand.title.includes('worktree'));
    assert.ok(bloomCommand.title.includes('claude'));
  });

  test('View container should be registered', () => {
    const extension = vscode.extensions.getExtension('gadugi.gadugi-vscode-extension');
    assert.ok(extension);
    
    const packageJson = extension.packageJSON;
    const viewContainers = packageJson.contributes?.viewsContainers?.activitybar;
    assert.ok(viewContainers);
    
    const gadugiContainer = viewContainers.find((container: any) => container.id === 'gadugi');
    assert.ok(gadugiContainer);
    assert.strictEqual(gadugiContainer.title, 'Gadugi');
  });
});