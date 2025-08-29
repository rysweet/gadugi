#!/bin/bash
# check-updates.sh - Check for agent updates functionality

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_MANAGER_ROOT="$(dirname "$SCRIPT_DIR")"

# Cache directory for update checks
CACHE_DIR="$AGENT_MANAGER_ROOT/cache"
REGISTRY_FILE="$CACHE_DIR/agent-registry.json"
TIMESTAMP_FILE="$CACHE_DIR/last-check-timestamp"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create cache directory if it doesn't exist
ensure_cache_dir() {
    mkdir -p "$CACHE_DIR"
}

# Get the last update check timestamp
get_last_check_timestamp() {
    if [ -f "$TIMESTAMP_FILE" ]; then
        cat "$TIMESTAMP_FILE"
    else
        echo "never"
    fi
}

# Update the last check timestamp
update_check_timestamp() {
    ensure_cache_dir
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "$TIMESTAMP_FILE"
}

# Check if we should perform an update check (default: every 24 hours)
should_check_updates() {
    local last_check=$(get_last_check_timestamp)

    if [ "$last_check" = "never" ]; then
        return 0
    fi

    # Check if 24 hours have passed since last check
    local last_timestamp=$(date -d "$last_check" +%s 2>/dev/null || echo 0)
    local current_timestamp=$(date +%s)
    local hours_passed=$(( (current_timestamp - last_timestamp) / 3600 ))

    if [ $hours_passed -ge 24 ]; then
        return 0
    else
        return 1
    fi
}

# Parse version string (e.g., "1.0.0" -> 10000 for comparison)
version_to_number() {
    local version=$1
    echo "$version" | awk -F. '{printf "%d%03d%03d", $1, $2, $3}'
}

# Compare two versions
compare_versions() {
    local version1=$1
    local version2=$2

    local num1=$(version_to_number "$version1")
    local num2=$(version_to_number "$version2")

    if [ "$num1" -gt "$num2" ]; then
        echo "1"  # version1 is newer
    elif [ "$num1" -lt "$num2" ]; then
        echo "-1" # version2 is newer
    else
        echo "0"  # versions are equal
    fi
}

# Get installed agents
get_installed_agents() {
    local agents_dir="$AGENT_MANAGER_ROOT/../agents"
    if [ -d "$agents_dir" ]; then
        find "$agents_dir" -name "*.md" -type f | while read -r agent_file; do
            local agent_name=$(basename "$agent_file" .md)
            # Skip the agent-manager itself
            if [ "$agent_name" != "agent-manager" ]; then
                echo "$agent_name"
            fi
        done
    fi
}

# Get agent version from metadata
get_agent_version() {
    local agent_name=$1
    local metadata_file="$AGENT_MANAGER_ROOT/../agents/$agent_name.md"

    if [ -f "$metadata_file" ]; then
        # Look for version in frontmatter
        local version=$(grep -m1 "^version:" "$metadata_file" 2>/dev/null | sed 's/version: *//')
        if [ -n "$version" ]; then
            echo "$version"
        else
            echo "unknown"
        fi
    else
        echo "not_found"
    fi
}

# Fetch latest registry information
fetch_registry() {
    ensure_cache_dir

    # For now, use a mock registry. In a real implementation, this would fetch from a remote source
    cat > "$REGISTRY_FILE" <<EOF
{
  "agents": {
    "workflow-master": {
      "latest_version": "2.0.0",
      "description": "Master workflow orchestration agent",
      "release_date": "2024-03-15"
    },
    "CodeReviewer": {
      "latest_version": "1.5.0",
      "description": "Automated code review agent",
      "release_date": "2024-03-10"
    },
    "TaskAnalyzer": {
      "latest_version": "1.2.0",
      "description": "Task analysis and decomposition agent",
      "release_date": "2024-03-05"
    }
  },
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
}

# Check for updates for a specific agent
check_agent_update() {
    local agent_name=$1
    local current_version=$2

    if [ ! -f "$REGISTRY_FILE" ]; then
        return 1
    fi

    # Extract latest version from registry
    local latest_version=$(jq -r ".agents[\"$agent_name\"].latest_version // \"unknown\"" "$REGISTRY_FILE" 2>/dev/null || echo "unknown")

    if [ "$latest_version" = "unknown" ]; then
        return 1
    fi

    local comparison=$(compare_versions "$current_version" "$latest_version")

    if [ "$comparison" = "-1" ]; then
        echo "$latest_version"
        return 0
    else
        return 1
    fi
}

# Main function to check for updates
check_for_updates() {
    local force_check=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force|-f)
                force_check=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    echo -e "${BLUE}🔍 Checking for agent updates...${NC}"

    # Check if we should perform update check
    if [ "$force_check" = false ] && ! should_check_updates; then
        local last_check=$(get_last_check_timestamp)
        echo -e "${YELLOW}⏭️  Skipping update check (last check: $last_check)${NC}"
        echo -e "${YELLOW}   Use --force to check anyway${NC}"
        return 0
    fi

    # Fetch latest registry
    echo "📥 Fetching latest agent registry..."
    fetch_registry

    # Update timestamp
    update_check_timestamp

    # Check installed agents
    echo -e "\n${BLUE}📦 Installed agents:${NC}"

    local updates_available=0
    local agents_checked=0

    # Check each installed agent
    while IFS= read -r agent_name; do
        if [ -n "$agent_name" ]; then
            ((agents_checked++))
            local current_version=$(get_agent_version "$agent_name")

            if [ "$current_version" = "not_found" ]; then
                echo -e "  ${RED}❌ $agent_name - not found${NC}"
            elif [ "$current_version" = "unknown" ]; then
                echo -e "  ${YELLOW}⚠️  $agent_name - version unknown${NC}"
            else
                local new_version=$(check_agent_update "$agent_name" "$current_version")
                if [ -n "$new_version" ]; then
                    echo -e "  ${YELLOW}📦 $agent_name: $current_version → $new_version (update available)${NC}"
                    ((updates_available++))
                else
                    echo -e "  ${GREEN}✅ $agent_name: $current_version (up to date)${NC}"
                fi
            fi
        fi
    done < <(get_installed_agents)

    # Summary
    echo -e "\n${BLUE}📊 Summary:${NC}"
    echo "  • Agents checked: $agents_checked"
    echo "  • Updates available: $updates_available"

    if [ $updates_available -gt 0 ]; then
        echo -e "\n${YELLOW}💡 To update agents, use:${NC}"
        echo "  /agent:agent-manager update <agent-name>"
    fi

    return 0
}

# Export the main function if sourced
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    export -f check_for_updates
fi
