#!/bin/bash
# Script to resolve merge conflicts for critical infrastructure PRs

echo "=========================================="
echo "RESOLVING CONFLICTS FOR CRITICAL PRs"
echo "=========================================="
echo ""

# Function to resolve conflicts for a specific file
resolve_conflicts() {
    local file=$1
    local strategy=$2  # "ours" or "theirs"
    
    if [ -f "$file" ]; then
        echo "  Resolving $file with strategy: $strategy"
        if [ "$strategy" = "theirs" ]; then
            git checkout --theirs "$file"
        else
            git checkout --ours "$file"
        fi
        git add "$file"
    fi
}

# Process each critical PR
for PR in 287 280 278; do
    echo "----------------------------------------"
    echo "Processing PR #$PR"
    echo "----------------------------------------"
    
    # Get branch name
    BRANCH=$(gh pr view $PR --json headRefName --jq '.headRefName')
    
    echo "Branch: $BRANCH"
    
    # Checkout PR
    echo "Checking out PR #$PR..."
    gh pr checkout $PR 2>/dev/null || git checkout $BRANCH || {
        echo "Failed to checkout PR #$PR"
        continue
    }
    
    # Fetch latest
    git fetch origin feature/gadugi-v0.3-regeneration
    
    # Attempt merge
    echo "Attempting merge..."
    git merge origin/feature/gadugi-v0.3-regeneration --no-edit || {
        echo "Merge has conflicts, resolving..."
        
        # Get list of conflicted files
        CONFLICTS=$(git status --porcelain | grep "^UU" | awk '{print $2}')
        
        if [ -n "$CONFLICTS" ]; then
            echo "Found conflicts in:"
            echo "$CONFLICTS"
            
            # Resolution strategy:
            # - Keep PR changes for implementation files
            # - Take v0.3 for dependencies and tests
            
            for file in $CONFLICTS; do
                case "$file" in
                    *Memory.md|*pyproject.toml|*uv.lock|*.secrets.baseline)
                        resolve_conflicts "$file" "theirs"
                        ;;
                    *test_*)
                        resolve_conflicts "$file" "theirs"
                        ;;
                    *)
                        # Keep PR changes for implementation files
                        resolve_conflicts "$file" "ours"
                        ;;
                esac
            done
            
            # Commit the resolution
            git commit -m "Merge feature/gadugi-v0.3-regeneration into PR #$PR
            
Resolved conflicts by:
- Keeping implementation changes from PR
- Taking v0.3 versions for dependencies
- Updating test files to v0.3" || true
            
            # Push changes
            echo "Pushing resolved conflicts..."
            git push || echo "Push failed for PR #$PR"
        fi
    }
    
    echo "PR #$PR processing complete"
    echo ""
done

# Return to v0.3 branch
git checkout feature/gadugi-v0.3-regeneration

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
for pr in 287 280 278; do
    mergeable=$(gh pr view $pr --json mergeable --jq '.mergeable')
    echo "PR #$pr: $mergeable"
done
