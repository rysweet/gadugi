import * as assert from 'assert';
import { PathUtils } from '../../utils/pathUtils';

suite('PathUtils Test Suite', () => {
  test('normalize should handle different path formats', () => {
    const windowsPath = 'C:\\Users\\test\\project';
    const unixPath = '/home/test/project';

    assert.ok(PathUtils.normalize(windowsPath));
    assert.ok(PathUtils.normalize(unixPath));
  });

  test('getBasename should extract directory/file name', () => {
    assert.strictEqual(PathUtils.getBasename('/path/to/directory'), 'directory');
    assert.strictEqual(PathUtils.getBasename('/path/to/file.txt'), 'file.txt');
    assert.strictEqual(PathUtils.getBasename('simple'), 'simple');
  });

  test('getDisplayPath should truncate long paths', () => {
    const longPath = '/very/long/path/that/should/be/truncated/to/show/only/end';
    const displayPath = PathUtils.getDisplayPath(longPath, 20);

    assert.ok(displayPath.length <= 20);
    assert.ok(displayPath.includes('...'));
  });

  test('getWorktreeName should extract worktree names', () => {
    assert.strictEqual(PathUtils.getWorktreeName('/project/.worktrees/feature-branch'), 'feature-branch');
    assert.strictEqual(PathUtils.getWorktreeName('/project/main'), 'main');
    assert.strictEqual(PathUtils.getWorktreeName('/project'), 'project');
  });

  test('sanitizeForIdentifier should clean path for identifiers', () => {
    const dirtyPath = '/path/with spaces/and-symbols!@#';
    const clean = PathUtils.sanitizeForIdentifier(dirtyPath);

    assert.ok(/^[a-zA-Z0-9\-_]+$/.test(clean));
    assert.ok(!clean.includes(' '));
  });

  test('isWorktreeSubdirectory should detect worktree paths', () => {
    assert.ok(PathUtils.isWorktreeSubdirectory('/project/.worktrees/branch'));
    assert.ok(PathUtils.isWorktreeSubdirectory('/project/worktrees/branch'));
    assert.ok(!PathUtils.isWorktreeSubdirectory('/project/src'));
  });
});
