# Git Workflow Best Practices

## Branch Management

### Branch Naming Conventions
- `feature/short-description` - New features
- `fix/issue-number-description` - Bug fixes
- `chore/maintenance-task` - Maintenance tasks
- `refactor/component-name` - Refactoring work
- `docs/section-updated` - Documentation updates

### Git Flow Best Practices
1. **Always branch from main/master**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/new-feature
   ```

2. **Keep commits atomic and descriptive**
   ```bash
   git commit -m "feat: add user authentication endpoint"
   git commit -m "fix: resolve token validation edge case"
   ```

3. **Regular rebasing to keep history clean**
   ```bash
   git rebase main
   git push --force-with-lease origin feature-branch
   ```

## Commit Message Conventions

### Format: `type(scope): description`

#### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

#### Examples
```
feat(auth): implement JWT token validation
fix(api): handle null values in user profile endpoint
docs(readme): update installation instructions
test(auth): add integration tests for login flow
refactor(utils): extract common validation functions
```

## Worktree Management

### Creating Worktrees for Isolation
```bash
# Create a new worktree for feature development
git worktree add ../feature-work feature/new-feature

# List all worktrees
git worktree list

# Remove worktree when done
git worktree remove ../feature-work
```

### Benefits of Worktrees
- Work on multiple features simultaneously
- Avoid losing work when switching branches
- Isolated testing environments
- Faster context switching

## Conflict Resolution

### Merge Conflict Strategies
1. **Preventive measures**
   - Frequent pulls from main
   - Small, focused changes
   - Communication with team

2. **Resolution workflow**
   ```bash
   git pull origin main
   # Resolve conflicts in editor
   git add .
   git commit -m "resolve: merge conflicts with main"
   ```

3. **Tools for complex conflicts**
   - `git mergetool`
   - VS Code merge editor
   - Beyond Compare, Meld, etc.

## Advanced Git Techniques

### Interactive Rebase for Clean History
```bash
# Rebase last 3 commits interactively
git rebase -i HEAD~3

# Options:
# pick - use commit
# reword - use commit but edit message
# edit - use commit but stop for amending
# squash - use commit but meld into previous commit
# fixup - like squash but discard commit message
```

### Cherry-picking for Selective Changes
```bash
# Pick specific commit from another branch
git cherry-pick <commit-hash>

# Pick range of commits
git cherry-pick <start-commit>..<end-commit>
```

### Stashing for Context Switching
```bash
# Stash current work
git stash push -m "work in progress on feature X"

# List stashes
git stash list

# Apply specific stash
git stash apply stash@{1}

# Pop latest stash (apply and remove)
git stash pop
```

## Branch Protection Rules

### Recommended Settings
- Require PR reviews (2+ reviewers)
- Require status checks to pass
- Require branches to be up to date before merging
- Restrict pushes to main branch
- Require signed commits for sensitive repos

### Status Checks Integration
- CI/CD pipeline checks
- Code quality gates (linting, type checking)
- Security scans
- Test coverage requirements

## Git Hooks for Automation

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Example .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

### Commit Message Hooks
- Enforce conventional commit format
- Check for issue references
- Validate commit message length

## Error Recovery

### Common Git Problems and Solutions

#### Accidental Commits
```bash
# Undo last commit but keep changes
git reset HEAD~1

# Undo last commit and discard changes
git reset --hard HEAD~1

# Amend last commit
git commit --amend -m "corrected commit message"
```

#### Lost Work Recovery
```bash
# Find lost commits
git reflog

# Recover from reflog
git checkout <commit-hash>
git branch recovery-branch

# Restore deleted branch
git branch <branch-name> <commit-hash>
```

#### Corrupted Repository
```bash
# Check repository integrity
git fsck --full

# Cleanup unnecessary files
git gc --aggressive --prune=now

# Reset to clean state
git clean -fdx
git reset --hard HEAD
```

## Performance Optimization

### Large Repository Management
```bash
# Shallow clone for faster downloads
git clone --depth 1 <repository-url>

# Partial clone to exclude large files
git clone --filter=blob:none <repository-url>

# Enable file system monitor for faster status
git config core.fsmonitor true
```

### Git LFS for Large Files
```bash
# Install and initialize Git LFS
git lfs install

# Track large files
git lfs track "*.zip"
git lfs track "*.pdf"

# Check LFS status
git lfs ls-files
```

## Collaboration Best Practices

### Code Review Workflow
1. Create feature branch
2. Implement changes with tests
3. Create pull request with descriptive title/body
4. Request appropriate reviewers
5. Address feedback promptly
6. Squash merge when approved

### Communication Guidelines
- Reference issues in commit messages (`fixes #123`)
- Use descriptive PR titles and descriptions
- Tag relevant team members for reviews
- Document breaking changes clearly
- Update documentation with code changes

## Security Considerations

### Sensitive Data Protection
```bash
# Remove sensitive data from history
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch path/to/sensitive/file' \
--prune-empty --tag-name-filter cat -- --all

# Use .gitignore for common sensitive files
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "secrets/" >> .gitignore
```

### GPG Signing for Authentication
```bash
# Configure GPG signing
git config --global user.signingkey <key-id>
git config --global commit.gpgsign true

# Sign individual commits
git commit -S -m "signed commit message"
```

## Automation and Tooling

### Git Aliases for Efficiency
```bash
# Add useful aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.lg "log --oneline --graph --decorate"
git config --global alias.unstage 'reset HEAD --'
```

### Integration with IDEs
- VS Code Git integration
- IntelliJ Git tools
- Command line tools (tig, gitk, git-gui)

This comprehensive guide covers essential Git workflows and best practices for professional software development.
