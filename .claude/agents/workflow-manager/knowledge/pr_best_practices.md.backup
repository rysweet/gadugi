# PR Best Practices

## Creating Effective Pull Requests

### PR Title Format
- Use conventional commits format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Keep under 50 characters
- Use imperative mood ("Add feature" not "Added feature")

### PR Description Structure
1. **Summary**: 2-3 sentences explaining the change
2. **Motivation**: Why is this change needed?
3. **Changes**: Bullet points of what was modified
4. **Testing**: How was this tested?
5. **Screenshots**: If UI changes (before/after)

### Common Review Points
- Code follows project style guidelines
- Tests are included and passing
- Documentation is updated
- No console.log or debug code left
- Error handling is comprehensive
- Performance impact is considered

### Size Guidelines
- Ideal PR: < 400 lines changed
- If larger, consider breaking into multiple PRs
- Each PR should be one logical change

### Branch Naming
- feature/description-of-feature
- fix/issue-number-description
- chore/task-description

### Commit Messages
- Each commit should be atomic (one logical change)
- Write descriptive commit messages
- Reference issue numbers when applicable

### Review Response
- Respond to all comments
- Mark resolved conversations
- Push fixes as new commits (squash later)
- Thank reviewers for their time

## Common Pitfalls to Avoid
1. Mixing refactoring with feature changes
2. Forgetting to update tests
3. Leaving commented-out code
4. Not running linter before push
5. Ignoring CI failures
6. Force pushing during review

## Automation Opportunities
- Pre-commit hooks for linting
- CI checks for tests
- Automated PR description templates
- Branch protection rules
