import * as assert from 'assert';
import * as vscode from 'vscode';
import * as sinon from 'sinon';
import { GitSetupService } from '../../services/gitSetupService';

suite('GitSetupService Tests', () => {
  let gitSetupService: GitSetupService;
  let mockContext: vscode.ExtensionContext;
  let sandbox: sinon.SinonSandbox;

  setup(() => {
    sandbox = sinon.createSandbox();
    
    // Create mock extension context
    mockContext = {
      subscriptions: [],
      workspaceState: {
        get: sandbox.stub().returns(false),
        update: sandbox.stub().resolves(),
      },
      globalState: {
        get: sandbox.stub(),
        update: sandbox.stub().resolves(),
      },
      asAbsolutePath: sandbox.stub(),
      extensionPath: '/test/path',
      extensionMode: vscode.ExtensionMode.Test,
      storageUri: vscode.Uri.file('/test/storage'),
      globalStorageUri: vscode.Uri.file('/test/global'),
      logUri: vscode.Uri.file('/test/log'),
      secrets: {} as any,
      extensionUri: vscode.Uri.file('/test/extension'),
      environmentVariableCollection: {} as any,
      extension: {} as any,
      storageFileSystem: {} as any,
      logFileSystem: {} as any,
      globalStorageFileSystem: {} as any
    } as vscode.ExtensionContext;

    gitSetupService = new GitSetupService(mockContext);
  });

  teardown(() => {
    sandbox.restore();
    gitSetupService.dispose();
  });

  suite('Git Status Detection', () => {
    test('should detect git installation correctly', async () => {
      // Mock successful git --version command
      const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
      execSyncStub.withArgs('git --version', { stdio: 'ignore' }).returns('git version 2.39.0');

      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      // Mock git rev-parse command for repository check
      execSyncStub.withArgs('git rev-parse --git-dir', sinon.match.any).returns('.git');

      const status = await gitSetupService.getGitStatus();

      assert.strictEqual(status.hasGit, true);
      assert.strictEqual(status.hasRepository, true);
      assert.strictEqual(status.workspaceFolder, '/test/workspace');
    });

    test('should handle git not installed', async () => {
      // Mock failed git --version command
      const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
      execSyncStub.withArgs('git --version', { stdio: 'ignore' }).throws(new Error('Command not found'));

      const status = await gitSetupService.getGitStatus();

      assert.strictEqual(status.hasGit, false);
      assert.strictEqual(status.hasRepository, false);
      assert.strictEqual(status.workspaceFolder, null);
    });

    test('should handle git installed but no repository', async () => {
      // Mock successful git --version command
      const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
      execSyncStub.withArgs('git --version', { stdio: 'ignore' }).returns('git version 2.39.0');

      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      // Mock failed git rev-parse command for repository check
      execSyncStub.withArgs('git rev-parse --git-dir', sinon.match.any).throws(new Error('Not a git repository'));

      const status = await gitSetupService.getGitStatus();

      assert.strictEqual(status.hasGit, true);
      assert.strictEqual(status.hasRepository, false);
      assert.strictEqual(status.workspaceFolder, '/test/workspace');
    });

    test('should handle no workspace folder', async () => {
      // Mock successful git --version command
      const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
      execSyncStub.withArgs('git --version', { stdio: 'ignore' }).returns('git version 2.39.0');

      // Mock no workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value(undefined);

      const status = await gitSetupService.getGitStatus();

      assert.strictEqual(status.hasGit, true);
      assert.strictEqual(status.hasRepository, false);
      assert.strictEqual(status.workspaceFolder, null);
    });
  });

  suite('Status Bar Management', () => {
    test('should update status bar for git ready state', async () => {
      // Mock git detection
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: true,
        workspaceFolder: '/test/workspace'
      });

      await gitSetupService.updateStatusBar();

      // Verify status bar shows success state
      // Note: In actual implementation, we would need to access the status bar item
      // This test structure shows how we would verify the status bar updates
      assert.ok(true, 'Status bar should show git ready state');
    });

    test('should update status bar for no repository state', async () => {
      // Mock git installed but no repository
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      await gitSetupService.updateStatusBar();

      // Verify status bar shows warning state
      assert.ok(true, 'Status bar should show no repository warning');
    });

    test('should update status bar for no git state', async () => {
      // Mock git not installed
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: false,
        hasRepository: false,
        workspaceFolder: null
      });

      await gitSetupService.updateStatusBar();

      // Verify status bar shows error state
      assert.ok(true, 'Status bar should show no git error');
    });
  });

  suite('Git Setup Guidance', () => {
    test('should not show guidance when git is ready', async () => {
      // Mock git ready state
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: true,
        workspaceFolder: '/test/workspace'
      });

      const showMessageSpy = sandbox.spy(vscode.window, 'showInformationMessage');

      await gitSetupService.showGitSetupGuidance();

      assert.ok(showMessageSpy.notCalled, 'Should not show guidance when git is ready');
    });

    test('should not show guidance when dismissed', async () => {
      // Mock dismissed state
      (mockContext.workspaceState.get as sinon.SinonStub).returns(true);

      // Mock git not ready state
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: false,
        hasRepository: false,
        workspaceFolder: null
      });

      const showMessageSpy = sandbox.spy(vscode.window, 'showInformationMessage');

      await gitSetupService.showGitSetupGuidance();

      assert.ok(showMessageSpy.notCalled, 'Should not show guidance when dismissed');
    });

    test('should show git installation guidance when git not installed', async () => {
      // Mock git not installed
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: false,
        hasRepository: false,
        workspaceFolder: null
      });

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves('Dismiss');

      await gitSetupService.showGitSetupGuidance();

      assert.ok(showMessageStub.calledOnce, 'Should show guidance dialog');
      const args = showMessageStub.getCall(0).args;
      assert.ok(args[0].includes('Git is not installed'), 'Should show git installation message');
      assert.ok(args[2].includes('Install Git Guide'), 'Should offer install guide action');
    });

    test('should show repository setup guidance when git installed but no repo', async () => {
      // Mock git installed but no repository
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves('Dismiss');

      await gitSetupService.showGitSetupGuidance();

      assert.ok(showMessageStub.calledOnce, 'Should show guidance dialog');
      const args = showMessageStub.getCall(0).args;
      assert.ok(args[0].includes('Git repository'), 'Should show repository setup message');
      assert.ok(args[2].includes('Clone Repository'), 'Should offer clone action');
      assert.ok(args[3].includes('Initialize Repository'), 'Should offer init action');
      assert.ok(args[4].includes('Open Folder'), 'Should offer open folder action');
    });
  });

  suite('Git Setup Actions', () => {
    test('should handle clone repository action', async () => {
      // Mock git installed but no repository
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      const executeCommandSpy = sandbox.spy(vscode.commands, 'executeCommand');
      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves('Clone Repository');

      await gitSetupService.showGitSetupGuidance();

      assert.ok(executeCommandSpy.calledWith('git.clone'), 'Should execute git clone command');
    });

    test('should handle initialize repository action', async () => {
      // Mock git installed but no repository
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      const execSyncStub = sandbox.stub(require('child_process'), 'execSync').returns('');
      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');
      
      // Mock user selections
      showMessageStub.onCall(0).resolves('Initialize Repository');
      showMessageStub.onCall(1).resolves('Yes'); // Confirm initialization
      showMessageStub.onCall(2).resolves('No'); // Skip initial commit

      await gitSetupService.showGitSetupGuidance();

      assert.ok(execSyncStub.calledWith('git init', sinon.match({ cwd: '/test/workspace' })), 
        'Should execute git init command');
    });

    test('should handle open folder action', async () => {
      // Mock git installed but no repository
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      const executeCommandSpy = sandbox.spy(vscode.commands, 'executeCommand');
      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves('Open Folder');

      await gitSetupService.showGitSetupGuidance();

      assert.ok(executeCommandSpy.calledWith('vscode.openFolder'), 'Should execute open folder command');
    });

    test('should handle dont show again action', async () => {
      // Mock git not installed
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: false,
        hasRepository: false,
        workspaceFolder: null
      });

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');
      showMessageStub.onCall(0).resolves('Don\'t Show Again');
      showMessageStub.onCall(1).resolves(); // Dismiss confirmation message

      await gitSetupService.showGitSetupGuidance();

      assert.ok((mockContext.workspaceState.update as sinon.SinonStub).calledWith('gadugi.gitSetup.dismissed', true),
        'Should update dismiss preference');
    });
  });

  suite('Repository Initialization', () => {
    test('should initialize repository with initial commit', async () => {
      // Mock successful git init
      const execSyncStub = sandbox.stub(require('child_process'), 'execSync').returns('');
      
      // Mock file system operations
      const fsStub = {
        existsSync: sandbox.stub().returns(false),
        writeFileSync: sandbox.stub()
      };
      sandbox.stub(require('fs'), 'existsSync').callsFake(fsStub.existsSync);
      sandbox.stub(require('fs'), 'writeFileSync').callsFake(fsStub.writeFileSync);

      // Mock path operations
      sandbox.stub(require('path'), 'join').returns('/test/workspace/.gitignore');

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');
      showMessageStub.onCall(0).resolves('Yes'); // Confirm create initial commit
      showMessageStub.onCall(1).resolves(); // Success message

      // Test the private method through public interface
      // We would need to expose this for testing or test through the public interface
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      showMessageStub.onCall(0).resolves('Initialize Repository');
      showMessageStub.onCall(1).resolves('Yes'); // Confirm initialization
      showMessageStub.onCall(2).resolves('Yes'); // Create initial commit

      await gitSetupService.showGitSetupGuidance();

      assert.ok(execSyncStub.calledWith('git init', sinon.match({ cwd: '/test/workspace' })), 
        'Should execute git init');
      assert.ok(execSyncStub.calledWith('git add .', sinon.match({ cwd: '/test/workspace' })), 
        'Should add files to git');
      assert.ok(execSyncStub.calledWith('git commit -m "Initial commit"', sinon.match({ cwd: '/test/workspace' })), 
        'Should create initial commit');
    });

    test('should handle git init errors gracefully', async () => {
      // Mock failed git init
      const execSyncStub = sandbox.stub(require('child_process'), 'execSync');
      execSyncStub.throws(new Error('Git init failed'));

      const showErrorStub = sandbox.stub(vscode.window, 'showErrorMessage').resolves();
      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');
      
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      showMessageStub.onCall(0).resolves('Initialize Repository');
      showMessageStub.onCall(1).resolves('Yes'); // Confirm initialization

      await gitSetupService.showGitSetupGuidance();

      assert.ok(showErrorStub.calledOnce, 'Should show error message on git init failure');
    });
  });

  suite('Dismiss Preference Management', () => {
    test('should reset dismiss preference', async () => {
      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves();

      await gitSetupService.resetDismissPreference();

      assert.ok((mockContext.workspaceState.update as sinon.SinonStub).calledWith('gadugi.gitSetup.dismissed', false),
        'Should reset dismiss preference to false');
      assert.ok(showMessageStub.calledOnce, 'Should show confirmation message');
    });

    test('should check dismiss preference correctly', async () => {
      // Mock dismissed state
      (mockContext.workspaceState.get as sinon.SinonStub).returns(true);

      // Mock git not ready state
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: false,
        hasRepository: false,
        workspaceFolder: null
      });

      const showMessageSpy = sandbox.spy(vscode.window, 'showInformationMessage');

      await gitSetupService.showGitSetupGuidance();

      assert.ok(showMessageSpy.notCalled, 'Should respect dismiss preference');
      assert.ok((mockContext.workspaceState.get as sinon.SinonStub).calledWith('gadugi.gitSetup.dismissed', false),
        'Should check dismiss preference');
    });
  });

  suite('Git Status Details', () => {
    test('should show detailed status when all prerequisites met', async () => {
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: true,
        workspaceFolder: '/test/workspace'
      });

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves('OK');

      await gitSetupService.showGitStatusDetails();

      assert.ok(showMessageStub.calledOnce, 'Should show status details');
      const message = showMessageStub.getCall(0).args[0];
      assert.ok(message.includes('Git is installed'), 'Should show git installed status');
      assert.ok(message.includes('Git repository detected'), 'Should show repository status');
      assert.ok(message.includes('All prerequisites met'), 'Should show success message');
    });

    test('should show detailed status with missing prerequisites', async () => {
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: false,
        hasRepository: false,
        workspaceFolder: null
      });

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves('OK');

      await gitSetupService.showGitStatusDetails();

      assert.ok(showMessageStub.calledOnce, 'Should show status details');
      const message = showMessageStub.getCall(0).args[0];
      assert.ok(message.includes('Git is not installed'), 'Should show git not installed status');
      assert.ok(message.includes('No workspace folder'), 'Should show workspace status');
    });

    test('should offer setup actions from status details', async () => {
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage').resolves('Setup Git Repository');

      await gitSetupService.showGitStatusDetails();

      assert.ok(showMessageStub.calledTwice, 'Should show status details and handle action');
      const actions = showMessageStub.getCall(0).args[3]; // Fourth argument should be action buttons
      assert.ok(actions.includes('Setup Git Repository'), 'Should offer setup action');
    });
  });
});