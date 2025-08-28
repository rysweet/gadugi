#!/usr/bin/env python3
"""
Real-time PR Monitoring Dashboard for v0.3 Regeneration Branch
Shows status of all retargeted PRs with merge conflict detection
"""

import subprocess
import json
import time
import os
from datetime import datetime

# List of PRs to monitor
PR_NUMBERS = [247, 268, 269, 270, 278, 279, 280, 281, 282, 286, 287, 293, 294, 295]

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def run_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    except:
        return None

def get_pr_info(pr_number):
    """Get detailed PR information"""
    cmd = f"gh pr view {pr_number} --json number,title,baseRefName,mergeable,state,statusCheckRollup"
    output = run_command(cmd)
    if output:
        try:
            return json.loads(output)
        except:
            return None
    return None

def get_merge_status_symbol(mergeable):
    """Get symbol for merge status"""
    if mergeable == "MERGEABLE":
        return "✅"
    elif mergeable == "CONFLICTING":
        return "⚠️ "
    else:
        return "❓"

def get_check_status_symbol(checks):
    """Get symbol for CI checks"""
    if not checks:
        return "⏳"

    # Check for status
    for check in checks:
        if check.get("status") == "COMPLETED":
            if check.get("conclusion") == "SUCCESS":
                return "✅"
            elif check.get("conclusion") == "FAILURE":
                return "❌"
    return "⏳"

def display_dashboard():
    """Display the PR monitoring dashboard"""
    clear_screen()

    print("=" * 80)
    print("PR MONITORING DASHBOARD - v0.3 REGENERATION BRANCH")
    print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # Categories
    categories = {
        "Infrastructure": [287, 280, 278],
        "Pyright Fixes": [279, 270, 286, 293],
        "Features": [282, 281, 247],
        "Workflows": [295, 294, 269, 268]
    }

    for category, prs in categories.items():
        print(f"\n📁 {category.upper()}:")
        print("-" * 76)

        for pr_num in prs:
            info = get_pr_info(pr_num)
            if info:
                merge_symbol = get_merge_status_symbol(info.get("mergeable"))
                checks = info.get("statusCheckRollup", [])
                check_symbol = get_check_status_symbol(checks)

                title = info.get("title", "")[:50]
                base = info.get("baseRefName", "")

                # Truncate base branch name if too long
                if len(base) > 20:
                    base = "...v0.3-regeneration"

                print(f"PR #{pr_num:4} {merge_symbol} {check_symbol} | {title:50} | {base}")
            else:
                print(f"PR #{pr_num:4} ❓ | Unable to fetch info")

    print("\n" + "=" * 80)
    print("Legend: ✅ = OK, ⚠️ = Conflicts, ❌ = Failed, ⏳ = In Progress, ❓ = Unknown")
    print("Refreshing every 30 seconds... Press Ctrl+C to exit")

def main():
    """Main dashboard loop"""
    print("Starting PR Monitoring Dashboard...")
    print("Fetching initial data...")

    try:
        while True:
            display_dashboard()
            time.sleep(30)  # Refresh every 30 seconds
    except KeyboardInterrupt:
        print("\n\nDashboard stopped by user.")
        print("Goodbye!")

if __name__ == "__main__":
    main()
