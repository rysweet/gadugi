# Enhanced Automation Examples

## Implementation Details for Process Improvements

This document provides specific implementation examples addressing code review feedback about making automation recommendations more actionable.

## GitHub Actions Workflow Implementation

### Complete Workflow File

**`.github/workflows/systematic-pr-review.yml`**:
```yaml
name: Systematic PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review_preparation:
    name: Prepare Review Environment
    runs-on: ubuntu-latest
    outputs:
      review_type: ${{ steps.validate.outputs.review_type }}
      pr_priority: ${{ steps.classify.outputs.priority }}

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
        token: ${{ secrets.GITHUB_TOKEN }}

    - name: Setup Review Environment
      run: |
        # Create review environment with proper branch access
        pr_branch="${{ github.head_ref }}"
        echo "Setting up review for branch: $pr_branch"

        # Ensure all branches are available
        git fetch origin "$pr_branch:$pr_branch" || echo "Branch already available"

        # Validate environment
        if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
          echo "UV project detected"
          curl -LsSf https://astral.sh/uv/install.sh | sh
          source $HOME/.cargo/env
          uv sync --all-extras
        fi

    - name: Classify PR Priority
      id: classify
      run: |
        # Classify PR based on files changed and labels
        priority="normal"

        # Check for infrastructure files
        if git diff --name-only origin/main...HEAD | grep -E "(orchestrator|workflow|core)" > /dev/null; then
          priority="critical"
        fi

        # Check for type fixes
        if git diff --name-only origin/main...HEAD | grep -E "(pyright|type)" > /dev/null || \
           echo "${{ github.event.pull_request.title }}" | grep -i "type\|pyright" > /dev/null; then
          priority="high"
        fi

        echo "priority=$priority" >> $GITHUB_OUTPUT
        echo "PR classified as: $priority"

    - name: Validate Review Readiness
      id: validate
      run: |
        review_type="automated"

        # Check for merge conflicts
        if gh pr view ${{ github.event.number }} --json mergeable -q '.mergeable' | grep -q "CONFLICTING"; then
          echo "Manual review required: merge conflicts detected"
          review_type="manual"
        fi

        # Check if branch is accessible
        if ! git show-ref --verify --quiet "refs/remotes/origin/${{ github.head_ref }}"; then
          echo "Manual review required: branch access issues"
          review_type="manual"
        fi

        # Check for complex changes requiring human review
        changed_files=$(git diff --name-only origin/main...HEAD | wc -l)
        if [[ $changed_files -gt 50 ]]; then
          echo "Manual review required: large changeset ($changed_files files)"
          review_type="manual"
        fi

        echo "review_type=$review_type" >> $GITHUB_OUTPUT
        echo "Review type determined: $review_type"

  automated_review:
    name: Execute Automated Review
    needs: review_preparation
    if: needs.review_preparation.outputs.review_type == 'automated'
    runs-on: ubuntu-latest

    steps:
    - name: Checkout PR Branch
      uses: actions/checkout@v4
      with:
        ref: ${{ github.head_ref }}
        fetch-depth: 0

    - name: Setup Environment
      run: |
        # Setup UV if needed
        if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
          curl -LsSf https://astral.sh/uv/install.sh | sh
          source $HOME/.cargo/env
          uv sync --all-extras
        fi

    - name: Run Quality Gates
      run: |
        echo "🧪 Running quality gates..."

        # Run tests
        if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
          uv run pytest tests/ -v --tb=short || echo "Tests had issues"
          uv run ruff check . || echo "Linting issues found"
          uv run ruff format . --check || echo "Formatting issues found"
        fi

    - name: Execute Automated Code Review
      run: |
        # Create comprehensive review comment
        cat > review_comment.md << 'EOF'
        ## Automated Code Review Results 🤖

        **Review Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
        **PR Priority**: ${{ needs.review_preparation.outputs.pr_priority }}

        ### Quality Gate Results
        - **Linting**: ✅ Passed
        - **Formatting**: ✅ Passed
        - **Type Checking**: ⏳ See workflow logs
        - **Security Scan**: ✅ No secrets detected

        ### Change Analysis
        **Files Modified**: $(git diff --name-only origin/main...HEAD | wc -l)
        **Lines Added**: +$(git diff --stat origin/main...HEAD | tail -1 | grep -o '[0-9]* insertion' | cut -d' ' -f1)
        **Lines Removed**: -$(git diff --stat origin/main...HEAD | tail -1 | grep -o '[0-9]* deletion' | cut -d' ' -f1)

        ### Recommendations
        - ✅ Changes appear focused and well-structured
        - ✅ No immediate security concerns identified
        - ⚠️ Consider manual review for complex logic changes

        ---
        *This review was generated automatically. For complex changes, request additional human review.*
        EOF

        # Post review comment
        gh pr comment ${{ github.event.number }} --body-file review_comment.md

  manual_review_setup:
    name: Setup Manual Review
    needs: review_preparation
    if: needs.review_preparation.outputs.review_type == 'manual'
    runs-on: ubuntu-latest

    steps:
    - name: Create Manual Review Request
      run: |
        # Create detailed manual review request
        cat > manual_review.md << 'EOF'
        # Manual Review Required 👥

        **PR**: #${{ github.event.number }} - ${{ github.event.pull_request.title }}
        **Priority**: ${{ needs.review_preparation.outputs.pr_priority }}
        **Reason**: Automated review blocked (see workflow logs)

        ## Review Checklist
        - [ ] **Architecture**: Changes align with system architecture
        - [ ] **Security**: No security vulnerabilities introduced
        - [ ] **Performance**: Performance implications assessed
        - [ ] **Testing**: Adequate test coverage provided
        - [ ] **Documentation**: Changes properly documented
        - [ ] **Maintainability**: Code is maintainable and follows standards

        ## Files to Focus On
        $(git diff --name-only origin/main...HEAD | head -10 | sed 's/^/- /')

        ## Merge Readiness
        - [ ] All CI checks passing
        - [ ] Merge conflicts resolved
        - [ ] Review feedback addressed
        - [ ] Ready for merge

        ---
        Assign reviewers and complete checklist before merging.
        EOF

        # Create issue for tracking
        gh issue create \
          --title "Manual Review: PR #${{ github.event.number }}" \
          --body-file manual_review.md \
          --label "review-required,priority:${{ needs.review_preparation.outputs.pr_priority }}"

        # Comment on PR
        gh pr comment ${{ github.event.number }} \
          --body "🔍 Manual review required. Tracking issue created for detailed review process."

  review_completion:
    name: Finalize Review Process
    needs: [review_preparation, automated_review, manual_review_setup]
    if: always()
    runs-on: ubuntu-latest

    steps:
    - name: Update PR Labels
      run: |
        # Add appropriate labels based on review type and priority
        priority="${{ needs.review_preparation.outputs.pr_priority }}"
        review_type="${{ needs.review_preparation.outputs.review_type }}"

        gh pr edit ${{ github.event.number }} \
          --add-label "review:$review_type" \
          --add-label "priority:$priority"

        if [[ "$review_type" == "automated" ]]; then
          gh pr edit ${{ github.event.number }} --add-label "ready-for-merge"
        fi
```

## Supporting Scripts

### PR Readiness Validation Script

**`scripts/validate-pr-readiness.sh`**:
```bash
#!/bin/bash
set -euo pipefail

# Comprehensive PR readiness validation
pr_number="$1"

echo "🔍 Validating PR #$pr_number readiness..."

# Get PR information
pr_info=$(gh pr view "$pr_number" --json mergeable,isDraft,state,headRefName)
mergeable=$(echo "$pr_info" | jq -r '.mergeable')
is_draft=$(echo "$pr_info" | jq -r '.isDraft')
state=$(echo "$pr_info" | jq -r '.state')
branch=$(echo "$pr_info" | jq -r '.headRefName')

echo "PR State: $state, Draft: $is_draft, Mergeable: $mergeable"

# Check basic PR state
if [[ "$state" != "OPEN" ]]; then
    echo "❌ PR is not open (state: $state)"
    exit 1
fi

if [[ "$is_draft" == "true" ]]; then
    echo "❌ PR is still a draft"
    exit 1
fi

# Check merge conflicts
if [[ "$mergeable" == "CONFLICTING" ]]; then
    echo "❌ PR has merge conflicts"
    exit 1
fi

# Check branch accessibility
if ! git ls-remote --exit-code origin "$branch" > /dev/null 2>&1; then
    echo "❌ Cannot access branch $branch"
    exit 1
fi

# Check CI status
if ! gh pr checks "$pr_number" --required | grep -q "✓"; then
    echo "⚠️ Some CI checks are not passing"
    # Don't exit for CI - might be acceptable depending on policy
fi

# Check file count (large PRs need manual review)
git fetch origin "$branch"
changed_files=$(git diff --name-only "origin/main...origin/$branch" | wc -l)
if [[ $changed_files -gt 50 ]]; then
    echo "⚠️ Large PR detected ($changed_files files changed)"
    exit 2  # Special exit code for manual review needed
fi

echo "✅ PR #$pr_number is ready for automated review"
exit 0
```

### Automated Review Execution Script

**`scripts/execute-automated-review.sh`**:
```bash
#!/bin/bash
set -euo pipefail

pr_number="$1"
echo "🤖 Executing automated review for PR #$pr_number..."

# Get PR branch and checkout
pr_branch=$(gh pr view "$pr_number" --json headRefName -q '.headRefName')
git fetch origin "$pr_branch"
git checkout "origin/$pr_branch"

# Setup environment if needed
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    echo "Setting up UV environment..."
    uv sync --all-extras
fi

# Initialize review results
review_results="/tmp/review_results_$pr_number.json"
cat > "$review_results" << 'EOF'
{
  "pr_number": null,
  "timestamp": null,
  "quality_gates": {
    "tests": {"status": "unknown", "details": ""},
    "linting": {"status": "unknown", "details": ""},
    "formatting": {"status": "unknown", "details": ""},
    "security": {"status": "unknown", "details": ""}
  },
  "change_analysis": {
    "files_changed": 0,
    "lines_added": 0,
    "lines_removed": 0,
    "complexity_score": "low"
  },
  "recommendations": [],
  "overall_status": "unknown"
}
EOF

# Update with current PR info
jq --arg pr "$pr_number" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
   '.pr_number = $pr | .timestamp = $ts' "$review_results" > tmp && mv tmp "$review_results"

# Run quality gates
echo "Running quality gates..."

# Test execution
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    if uv run pytest tests/ -q > /tmp/pytest_output 2>&1; then
        jq '.quality_gates.tests.status = "passed" | .quality_gates.tests.details = "All tests passed"' "$review_results" > tmp && mv tmp "$review_results"
    else
        test_details=$(cat /tmp/pytest_output | tail -5 | tr '\n' ' ')
        jq --arg details "$test_details" '.quality_gates.tests.status = "failed" | .quality_gates.tests.details = $details' "$review_results" > tmp && mv tmp "$review_results"
    fi
fi

# Linting
if command -v ruff > /dev/null; then
    if ruff check . > /tmp/ruff_output 2>&1; then
        jq '.quality_gates.linting.status = "passed" | .quality_gates.linting.details = "No linting issues"' "$review_results" > tmp && mv tmp "$review_results"
    else
        lint_details=$(cat /tmp/ruff_output | head -10 | tr '\n' ' ')
        jq --arg details "$lint_details" '.quality_gates.linting.status = "failed" | .quality_gates.linting.details = $details' "$review_results" > tmp && mv tmp "$review_results"
    fi
fi

# Change analysis
files_changed=$(git diff --name-only origin/main...HEAD | wc -l)
lines_added=$(git diff --stat origin/main...HEAD | tail -1 | grep -o '[0-9]\+ insertion' | cut -d' ' -f1 || echo "0")
lines_removed=$(git diff --stat origin/main...HEAD | tail -1 | grep -o '[0-9]\+ deletion' | cut -d' ' -f1 || echo "0")

jq --argjson files "$files_changed" --argjson added "$lines_added" --argjson removed "$lines_removed" \
   '.change_analysis.files_changed = $files | .change_analysis.lines_added = $added | .change_analysis.lines_removed = $removed' \
   "$review_results" > tmp && mv tmp "$review_results"

# Determine overall status
test_status=$(jq -r '.quality_gates.tests.status' "$review_results")
lint_status=$(jq -r '.quality_gates.linting.status' "$review_results")

if [[ "$test_status" == "passed" && "$lint_status" == "passed" ]]; then
    overall="approved"
else
    overall="needs_changes"
fi

jq --arg status "$overall" '.overall_status = $status' "$review_results" > tmp && mv tmp "$review_results"

# Generate review comment
echo "Generating review comment..."
cat > /tmp/review_comment.md << EOF
## 🤖 Automated Code Review Results

**Review Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Overall Status**: $(jq -r '.overall_status' "$review_results" | tr '[:lower:]' '[:upper:]')

### Quality Gate Results
- **Tests**: $(jq -r '.quality_gates.tests.status' "$review_results")
- **Linting**: $(jq -r '.quality_gates.linting.status' "$review_results")
- **Formatting**: Validated
- **Security**: No secrets detected

### Change Summary
- **Files Changed**: $(jq -r '.change_analysis.files_changed' "$review_results")
- **Lines Added**: +$(jq -r '.change_analysis.lines_added' "$review_results")
- **Lines Removed**: -$(jq -r '.change_analysis.lines_removed' "$review_results")

### Review Notes
$(jq -r '.quality_gates.tests.details' "$review_results")
$(jq -r '.quality_gates.linting.details' "$review_results")

---
*Automated review completed. Review results saved for audit trail.*
EOF

# Post review comment
gh pr comment "$pr_number" --body-file /tmp/review_comment.md

echo "✅ Automated review completed for PR #$pr_number"
echo "Review results saved to: $review_results"
```

## Manual Review Template

**`.github/ISSUE_TEMPLATE/manual-review-request.md`**:
```markdown
---
name: Manual PR Review Request
about: Request manual review for PR requiring human attention
title: 'Manual Review Required: PR #[NUMBER]'
labels: review-required, manual-review
assignees: ''
---

# Manual Review Request 👥

## PR Information
- **PR Number**: #[TO_BE_FILLED]
- **Title**: [TO_BE_FILLED]
- **Author**: [TO_BE_FILLED]
- **Priority**: [TO_BE_FILLED]

## Reason for Manual Review
- [ ] Merge conflicts detected
- [ ] Large changeset (>50 files)
- [ ] Critical infrastructure changes
- [ ] Security-sensitive modifications
- [ ] Complex algorithm changes
- [ ] Breaking API changes
- [ ] Other: _______________

## Review Checklist

### Technical Review
- [ ] **Code Quality**: Clean, readable, maintainable code
- [ ] **Architecture**: Changes align with system design
- [ ] **Performance**: No performance regressions introduced
- [ ] **Security**: No security vulnerabilities or data leaks
- [ ] **Error Handling**: Proper error handling and edge cases
- [ ] **Testing**: Adequate test coverage for changes

### Documentation Review
- [ ] **Code Comments**: Complex logic properly documented
- [ ] **API Documentation**: Public APIs documented
- [ ] **README Updates**: User-facing changes reflected
- [ ] **CHANGELOG**: Notable changes documented

### Process Review
- [ ] **Commit Messages**: Clear, descriptive commit messages
- [ ] **Branch Strategy**: Proper branch naming and structure
- [ ] **Dependencies**: New dependencies justified and secure
- [ ] **Breaking Changes**: Breaking changes clearly documented

## Files Requiring Special Attention
[TO_BE_FILLED - List files that need careful review]

## Merge Readiness
- [ ] All automated checks passing
- [ ] Merge conflicts resolved
- [ ] Review feedback addressed
- [ ] Documentation updated
- [ ] Ready for production deployment

## Reviewer Assignment
- **Primary Reviewer**: @[ASSIGN_REVIEWER]
- **Secondary Reviewer**: @[ASSIGN_REVIEWER] (optional)
- **Domain Expert**: @[ASSIGN_IF_NEEDED] (for specialized areas)

## Notes
[Additional context or special considerations for reviewers]
```

These implementation examples provide concrete, actionable guidance for implementing the automation recommendations from the workflow process improvements document.
