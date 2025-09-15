#!/bin/bash
# Update all PRs with latest v0.3-regeneration branch

echo "=========================================="
echo "UPDATING ALL PRS WITH V0.3-REGENERATION"
echo "=========================================="
echo ""

# Array of PR numbers
PRS=(247 268 269 270 278 279 280 281 282 286 287 293 294 295)

# Counter for successes and failures
SUCCESS=0
FAILED=0
CONFLICTS=0

for PR in "${PRS[@]}"; do
    echo "----------------------------------------"
    echo "Processing PR #$PR..."

    # Get PR branch name
    BRANCH=$(gh pr view $PR --json headRefName --jq '.headRefName')

    if [ -z "$BRANCH" ]; then
        echo "❌ Failed to get branch name for PR #$PR"
        ((FAILED++))
        continue
    fi

    echo "Branch: $BRANCH"

    # Checkout the PR branch
    echo "Checking out PR #$PR..."
    gh pr checkout $PR 2>/dev/null || git checkout $BRANCH

    if [ $? -ne 0 ]; then
        echo "❌ Failed to checkout PR #$PR"
        ((FAILED++))
        continue
    fi

    # Fetch latest v0.3-regeneration
    echo "Fetching latest v0.3-regeneration..."
    git fetch origin feature/gadugi-v0.3-regeneration

    # Attempt to merge
    echo "Attempting to merge v0.3-regeneration..."
    git merge origin/feature/gadugi-v0.3-regeneration --no-edit

    if [ $? -eq 0 ]; then
        echo "✅ Successfully merged for PR #$PR"

        # Push the changes
        echo "Pushing updates..."
        git push origin $BRANCH

        if [ $? -eq 0 ]; then
            echo "✅ PR #$PR updated successfully!"
            ((SUCCESS++))
        else
            echo "⚠️  PR #$PR merged but push failed"
            ((CONFLICTS++))
        fi
    else
        echo "⚠️  PR #$PR has merge conflicts that need manual resolution"
        git merge --abort
        ((CONFLICTS++))
    fi

    echo ""
done

# Return to original branch
git checkout feature/gadugi-v0.3-regeneration

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo "✅ Successfully updated: $SUCCESS"
echo "⚠️  Have conflicts: $CONFLICTS"
echo "❌ Failed: $FAILED"
echo "Total PRs processed: ${#PRS[@]}"
echo ""

if [ $CONFLICTS -gt 0 ]; then
    echo "PRs with conflicts need manual resolution:"
    for PR in "${PRS[@]}"; do
        mergeable=$(gh pr view $PR --json mergeable --jq '.mergeable')
        if [ "$mergeable" = "CONFLICTING" ]; then
            echo "  - PR #$PR"
        fi
    done
fi
