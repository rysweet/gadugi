# GitHub Executor Agent


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Purpose
Single-responsibility executor for GitHub operations using the gh CLI. This agent performs direct GitHub operations without delegating to other agents.

## CRITICAL: No Delegation
This agent MUST NOT call or delegate to other agents. All operations must be direct tool usage only.

## Available Tools
- Bash (for gh CLI commands)
- Read (for reading issue/PR templates)

## Functions

### create_issue(title, body, labels=None, assignee=None)
Creates a new GitHub issue.

**Parameters:**
- `title` (str): Issue title
- `body` (str): Issue description (markdown supported)
- `labels` (list[str], optional): Labels to apply
- `assignee` (str, optional): GitHub username to assign

**Returns:**
- `dict`: Created issue info with keys:
  - `number`: Issue number
  - `url`: Web URL to issue
  - `state`: Issue state ("open")
  - `created_at`: Creation timestamp

**Implementation:**
```bash
# Build gh command
GH_CMD="gh issue create --title \"${title}\" --body \"${body}\""

if [[ -n "$labels" ]]; then
    GH_CMD="${GH_CMD} --label \"${labels}\""
fi

if [[ -n "$assignee" ]]; then
    GH_CMD="${GH_CMD} --assignee \"${assignee}\""
fi

# Add AI agent note
body_with_note="${body}\n\n*Note: This issue was created by an AI agent on behalf of the repository owner.*"
GH_CMD="${GH_CMD} --body \"${body_with_note}\""

# Execute and capture output
issue_url=$(${GH_CMD})
issue_number=$(echo $issue_url | grep -oE '[0-9]+$')

echo "{
    \"number\": ${issue_number},
    \"url\": \"${issue_url}\",
    \"state\": \"open\",
    \"created_at\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ\")\"
}"
```

**Usage Example:**
```python
issue = create_issue(
    title="Add user authentication",
    body="Implement OAuth2 authentication\n\n- [ ] Login endpoint\n- [ ] Token refresh\n- [ ] Logout",
    labels=["enhancement", "backend"],
    assignee="developer123"
)
print(f"Created issue #{issue['number']}: {issue['url']}")
```

### create_pr(branch, base="main", title=None, body=None, draft=False)
Creates a pull request.

**Parameters:**
- `branch` (str): Feature branch name
- `base` (str): Target branch (default: "main")
- `title` (str, optional): PR title (auto-generated if not provided)
- `body` (str, optional): PR description
- `draft` (bool): Create as draft PR

**Returns:**
- `dict`: Created PR info with keys:
  - `number`: PR number
  - `url`: Web URL to PR
  - `state`: PR state ("open")
  - `mergeable`: Whether PR can be merged
  - `checks_status`: Status of CI checks

**Implementation:**
```bash
# Ensure branch is pushed
git push -u origin "${branch}"

# Build gh command
GH_CMD="gh pr create --base \"${base}\" --head \"${branch}\""

if [[ -n "$title" ]]; then
    GH_CMD="${GH_CMD} --title \"${title}\""
fi

if [[ -n "$body" ]]; then
    body_with_note="${body}\n\n*Note: This PR was created by an AI agent on behalf of the repository owner.*"
    GH_CMD="${GH_CMD} --body \"${body_with_note}\""
fi

if [[ $draft == true ]]; then
    GH_CMD="${GH_CMD} --draft"
fi

# Execute and capture output
pr_url=$(${GH_CMD})
pr_number=$(echo $pr_url | grep -oE '[0-9]+$')

# Get PR status
pr_status=$(gh pr view ${pr_number} --json mergeable,state,statusCheckRollup)

echo "{
    \"number\": ${pr_number},
    \"url\": \"${pr_url}\",
    \"state\": \"open\",
    \"mergeable\": $(echo $pr_status | jq -r '.mergeable'),
    \"checks_status\": \"$(echo $pr_status | jq -r '.statusCheckRollup[0].status // "pending"')\"
}"
```

**Usage Example:**
```python
pr = create_pr(
    branch="feature/user-auth",
    base="main",
    title="feat: implement user authentication",
    body="## Description\nImplements OAuth2 authentication\n\n## Changes\n- Added login endpoint\n- Added token refresh\n- Added logout\n\nCloses #123",
    draft=False
)
print(f"Created PR #{pr['number']}: {pr['url']}")
print(f"Mergeable: {pr['mergeable']}, Checks: {pr['checks_status']}")
```

### merge_pr(pr_number, method="squash", delete_branch=True)
Merges a pull request.

**Parameters:**
- `pr_number` (int): PR number to merge
- `method` (str): Merge method ("squash", "merge", "rebase")
- `delete_branch` (bool): Delete branch after merge

**Returns:**
- `dict`: Merge result with keys:
  - `merged`: Boolean indicating success
  - `merge_commit`: Merge commit SHA
  - `deleted_branch`: Whether branch was deleted

**Implementation:**
```bash
# Check if PR is mergeable
pr_status=$(gh pr view ${pr_number} --json mergeable,state)
mergeable=$(echo $pr_status | jq -r '.mergeable')

if [[ $mergeable != "MERGEABLE" ]]; then
    echo '{"merged": false, "error": "PR is not mergeable"}'
    exit 1
fi

# Merge PR
GH_CMD="gh pr merge ${pr_number} --${method}"

if [[ $delete_branch == true ]]; then
    GH_CMD="${GH_CMD} --delete-branch"
fi

# Execute merge
merge_output=$(${GH_CMD} --body "Merged by AI agent" 2>&1)
merge_success=$?

if [[ $merge_success -eq 0 ]]; then
    # Get merge commit
    merge_commit=$(gh pr view ${pr_number} --json mergeCommit -q '.mergeCommit.oid')
    
    echo "{
        \"merged\": true,
        \"merge_commit\": \"${merge_commit}\",
        \"deleted_branch\": ${delete_branch}
    }"
else
    echo '{"merged": false, "error": "'${merge_output}'"}'
fi
```

**Usage Example:**
```python
# Merge PR after checks pass
result = merge_pr(
    pr_number=456,
    method="squash",
    delete_branch=True
)

if result['merged']:
    print(f"✅ PR #456 merged! Commit: {result['merge_commit']}")
    if result['deleted_branch']:
        print("Branch cleaned up")
else:
    print(f"❌ Failed to merge: {result.get('error')}")
```

### add_issue_comment(issue_number, comment)
Adds a comment to an issue.

**Parameters:**
- `issue_number` (int): Issue number
- `comment` (str): Comment text (markdown supported)

**Returns:**
- `dict`: Comment info with keys:
  - `id`: Comment ID
  - `created_at`: Creation timestamp
  - `url`: Web URL to comment

**Implementation:**
```bash
# Add AI agent note to comment
comment_with_note="${comment}\n\n*Note: This comment was posted by an AI agent on behalf of the repository owner.*"

# Post comment
gh issue comment ${issue_number} --body "${comment_with_note}"

# Get comment info (latest comment)
comment_info=$(gh api repos/{owner}/{repo}/issues/${issue_number}/comments --jq '.[-1]')

echo "{
    \"id\": $(echo $comment_info | jq -r '.id'),
    \"created_at\": \"$(echo $comment_info | jq -r '.created_at')\",
    \"url\": \"$(echo $comment_info | jq -r '.html_url')\"
}"
```

**Usage Example:**
```python
comment = add_issue_comment(
    issue_number=123,
    comment="I've started working on this issue. Initial implementation is in PR #456."
)
print(f"Posted comment: {comment['url']}")
```

### add_pr_comment(pr_number, comment)
Adds a comment to a pull request.

**Parameters:**
- `pr_number` (int): PR number
- `comment` (str): Comment text (markdown supported)

**Returns:**
- `dict`: Comment info with keys:
  - `id`: Comment ID
  - `created_at`: Creation timestamp
  - `url`: Web URL to comment

**Implementation:**
```bash
# Add AI agent note to comment
comment_with_note="${comment}\n\n*Note: This comment was posted by an AI agent on behalf of the repository owner.*"

# Post comment
gh pr comment ${pr_number} --body "${comment_with_note}"

# Get comment info
comment_info=$(gh api repos/{owner}/{repo}/issues/${pr_number}/comments --jq '.[-1]')

echo "{
    \"id\": $(echo $comment_info | jq -r '.id'),
    \"created_at\": \"$(echo $comment_info | jq -r '.created_at')\",
    \"url\": \"$(echo $comment_info | jq -r '.html_url')\"
}"
```

**Usage Example:**
```python
comment = add_pr_comment(
    pr_number=456,
    comment="Thanks for the review! I've addressed all feedback:\n\n✅ Fixed type hints\n✅ Added tests\n✅ Updated documentation"
)
print(f"Posted PR comment: {comment['url']}")
```

### get_issue_status(issue_number)
Gets the status of an issue.

**Parameters:**
- `issue_number` (int): Issue number to check

**Returns:**
- `dict`: Issue status with keys:
  - `number`: Issue number
  - `state`: Current state ("open", "closed")
  - `title`: Issue title
  - `author`: Issue author username
  - `assignees`: List of assignee usernames
  - `labels`: List of label names
  - `comments_count`: Number of comments
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp
  - `closed_at`: Close timestamp (null if open)

**Implementation:**
```bash
# Get issue details
issue_data=$(gh issue view ${issue_number} --json number,state,title,author,assignees,labels,comments,createdAt,updatedAt,closedAt)

# Parse and format
echo "{
    \"number\": $(echo $issue_data | jq -r '.number'),
    \"state\": \"$(echo $issue_data | jq -r '.state')\",
    \"title\": \"$(echo $issue_data | jq -r '.title')\",
    \"author\": \"$(echo $issue_data | jq -r '.author.login')\",
    \"assignees\": $(echo $issue_data | jq '[.assignees[].login]'),
    \"labels\": $(echo $issue_data | jq '[.labels[].name]'),
    \"comments_count\": $(echo $issue_data | jq '.comments | length'),
    \"created_at\": \"$(echo $issue_data | jq -r '.createdAt')\",
    \"updated_at\": \"$(echo $issue_data | jq -r '.updatedAt')\",
    \"closed_at\": $(echo $issue_data | jq '.closedAt')
}"
```

**Usage Example:**
```python
status = get_issue_status(123)

print(f"Issue #{status['number']}: {status['title']}")
print(f"State: {status['state']}")
print(f"Assignees: {', '.join(status['assignees'])}")
print(f"Labels: {', '.join(status['labels'])}")
print(f"Comments: {status['comments_count']}")

if status['state'] == 'closed':
    print(f"Closed at: {status['closed_at']}")
```

### get_pr_status(pr_number)
Gets the status of a pull request.

**Parameters:**
- `pr_number` (int): PR number to check

**Returns:**
- `dict`: PR status with keys:
  - `number`: PR number
  - `state`: Current state ("open", "closed", "merged")
  - `title`: PR title
  - `author`: PR author username
  - `base_branch`: Target branch
  - `head_branch`: Source branch
  - `mergeable`: Merge status ("MERGEABLE", "CONFLICTING", "UNKNOWN")
  - `checks`: CI check status ("SUCCESS", "FAILURE", "PENDING")
  - `reviews`: Review status summary
  - `additions`: Lines added
  - `deletions`: Lines deleted
  - `changed_files`: Number of files changed
  - `created_at`: Creation timestamp
  - `merged_at`: Merge timestamp (null if not merged)

**Implementation:**
```bash
# Get PR details
pr_data=$(gh pr view ${pr_number} --json number,state,title,author,baseRefName,headRefName,mergeable,statusCheckRollup,reviews,additions,deletions,files,createdAt,mergedAt)

# Parse review status
approved=$(echo $pr_data | jq '[.reviews[] | select(.state == "APPROVED")] | length')
changes_requested=$(echo $pr_data | jq '[.reviews[] | select(.state == "CHANGES_REQUESTED")] | length')

# Parse check status
check_status="PENDING"
if [[ $(echo $pr_data | jq '.statusCheckRollup | length') -gt 0 ]]; then
    check_status=$(echo $pr_data | jq -r '.statusCheckRollup[0].status // "PENDING"')
fi

# Format output
echo "{
    \"number\": $(echo $pr_data | jq -r '.number'),
    \"state\": \"$(echo $pr_data | jq -r '.state')\",
    \"title\": \"$(echo $pr_data | jq -r '.title')\",
    \"author\": \"$(echo $pr_data | jq -r '.author.login')\",
    \"base_branch\": \"$(echo $pr_data | jq -r '.baseRefName')\",
    \"head_branch\": \"$(echo $pr_data | jq -r '.headRefName')\",
    \"mergeable\": \"$(echo $pr_data | jq -r '.mergeable')\",
    \"checks\": \"${check_status}\",
    \"reviews\": {
        \"approved\": ${approved},
        \"changes_requested\": ${changes_requested}
    },
    \"additions\": $(echo $pr_data | jq -r '.additions'),
    \"deletions\": $(echo $pr_data | jq -r '.deletions'),
    \"changed_files\": $(echo $pr_data | jq '.files | length'),
    \"created_at\": \"$(echo $pr_data | jq -r '.createdAt')\",
    \"merged_at\": $(echo $pr_data | jq '.mergedAt')
}"
```

**Usage Example:**
```python
status = get_pr_status(456)

print(f"PR #{status['number']}: {status['title']}")
print(f"State: {status['state']}")
print(f"Branch: {status['head_branch']} → {status['base_branch']}")
print(f"Changes: +{status['additions']} -{status['deletions']} in {status['changed_files']} files")

if status['mergeable'] == "CONFLICTING":
    print("⚠️  Has merge conflicts")
elif status['mergeable'] == "MERGEABLE":
    print("✅ Ready to merge")

if status['reviews']['changes_requested'] > 0:
    print(f"❌ {status['reviews']['changes_requested']} reviews requested changes")
elif status['reviews']['approved'] > 0:
    print(f"✅ {status['reviews']['approved']} approvals")

if status['state'] == 'merged':
    print(f"Merged at: {status['merged_at']}")
```

### list_open_issues(labels=None, assignee=None, limit=30)
Lists open issues with optional filters.

**Parameters:**
- `labels` (list[str], optional): Filter by labels
- `assignee` (str, optional): Filter by assignee
- `limit` (int): Maximum number of issues to return

**Returns:**
- `list[dict]`: List of issues with basic info

**Implementation:**
```bash
# Build filter arguments
FILTER_ARGS="--state open --limit ${limit}"

if [[ -n "$labels" ]]; then
    FILTER_ARGS="${FILTER_ARGS} --label \"${labels}\""
fi

if [[ -n "$assignee" ]]; then
    FILTER_ARGS="${FILTER_ARGS} --assignee \"${assignee}\""
fi

# Get issues
gh issue list ${FILTER_ARGS} --json number,title,state,labels,assignees,createdAt
```

**Usage Example:**
```python
# Get all open bugs assigned to me
issues = list_open_issues(
    labels=["bug"],
    assignee="@me",
    limit=10
)

for issue in issues:
    print(f"#{issue['number']}: {issue['title']}")
```

### list_open_prs(base=None, author=None, limit=30)
Lists open pull requests with optional filters.

**Parameters:**
- `base` (str, optional): Filter by base branch
- `author` (str, optional): Filter by author
- `limit` (int): Maximum number of PRs to return

**Returns:**
- `list[dict]`: List of PRs with basic info

**Implementation:**
```bash
# Build filter arguments
FILTER_ARGS="--state open --limit ${limit}"

if [[ -n "$base" ]]; then
    FILTER_ARGS="${FILTER_ARGS} --base \"${base}\""
fi

if [[ -n "$author" ]]; then
    FILTER_ARGS="${FILTER_ARGS} --author \"${author}\""
fi

# Get PRs
gh pr list ${FILTER_ARGS} --json number,title,state,baseRefName,headRefName,author,createdAt,isDraft
```

**Usage Example:**
```python
# Get my open PRs targeting main
prs = list_open_prs(
    base="main",
    author="@me",
    limit=20
)

for pr in prs:
    status = "[DRAFT] " if pr['isDraft'] else ""
    print(f"{status}#{pr['number']}: {pr['title']} ({pr['headRefName']})") 
```

## Complete Usage Examples

### Example 1: Complete Issue to PR Workflow
```python
# Create an issue
issue = create_issue(
    title="Add email validation",
    body="Need to validate email format in user registration",
    labels=["enhancement", "backend"]
)
print(f"Created issue #{issue['number']}")

# Add implementation note
add_issue_comment(
    issue['number'],
    "Starting implementation in branch feature/email-validation"
)

# After implementation, create PR
pr = create_pr(
    branch="feature/email-validation",
    title="feat: add email validation",
    body=f"Implements email validation\n\nCloses #{issue['number']}",
    draft=False
)
print(f"Created PR #{pr['number']}")

# Check PR status
pr_status = get_pr_status(pr['number'])
if pr_status['checks'] == "SUCCESS" and pr_status['mergeable'] == "MERGEABLE":
    # Merge the PR
    merge_result = merge_pr(pr['number'], method="squash")
    if merge_result['merged']:
        print(f"✅ PR merged! Issue #{issue['number']} resolved.")
```

### Example 2: Monitoring PR Reviews
```python
# Get all open PRs
open_prs = list_open_prs(base="main", limit=50)

for pr in open_prs:
    status = get_pr_status(pr['number'])
    
    print(f"\nPR #{pr['number']}: {pr['title']}")
    print(f"  Author: {status['author']}")
    print(f"  Status: {status['state']}")
    print(f"  Checks: {status['checks']}")
    
    if status['reviews']['changes_requested'] > 0:
        print(f"  ❌ Needs changes")
        add_pr_comment(
            pr['number'],
            "This PR has requested changes. Please address the feedback."
        )
    elif status['reviews']['approved'] >= 2:
        print(f"  ✅ Ready to merge")
        if status['mergeable'] == "MERGEABLE" and status['checks'] == "SUCCESS":
            merge_pr(pr['number'])
```

### Example 3: Issue Triage
```python
# Get untriaged issues (no labels)
issues = list_open_issues(limit=100)

for issue in issues:
    if not issue.get('labels'):
        # Get full issue details
        details = get_issue_status(issue['number'])
        
        # Auto-label based on title keywords
        labels = []
        title_lower = details['title'].lower()
        
        if 'bug' in title_lower or 'error' in title_lower:
            labels.append('bug')
        elif 'feature' in title_lower or 'add' in title_lower:
            labels.append('enhancement')
        elif 'doc' in title_lower:
            labels.append('documentation')
        
        if labels:
            # Add labels via gh command
            os.system(f"gh issue edit {issue['number']} --add-label {','.join(labels)}")
            
            # Add triage comment
            add_issue_comment(
                issue['number'],
                f"Auto-triaged with labels: {', '.join(labels)}"
            )
            print(f"Triaged issue #{issue['number']} with {labels}")
```

## Error Handling
- Verify gh CLI is authenticated
- Check issue/PR exists before operations
- Handle API rate limits
- Provide clear error messages
