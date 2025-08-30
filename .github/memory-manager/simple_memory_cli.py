#!/usr/bin/env python3
"""
Simple Memory CLI - Command-line interface for GitHub Issues-only memory management

This provides a streamlined CLI for the SimpleMemoryManager, replacing the complex
configuration and sync operations with straightforward GitHub Issues operations.
"""

import argparse
import json
import sys
import logging

from simple_memory_manager import SimpleMemoryManager


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def handle_status(manager: SimpleMemoryManager, args) -> int:
    """Handle status command"""
    status = manager.get_memory_status()

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        if status["success"]:
            issue_info = status["memory_issue"]
            content_info = status["memory_content"]

            print("🧠 Simple Memory Manager Status")
            print("=" * 40)
            print(f"Memory Issue: #{issue_info['number']} - {issue_info['title']}")
            print(f"State: {issue_info['state']}")
            print(f"URL: {issue_info['url']}")
            print(f"Created: {issue_info['created_at']}")
            print(f"Updated: {issue_info['updated_at']}")
            print()
            print(f"Total Memory Comments: {content_info['total_comments']}")
            print(f"Memory Sections: {', '.join(content_info['sections'])}")
            print()
            print("Section Breakdown:")
            for section, count in content_info["section_counts"].items():
                print(f"  {section}: {count} entries")
            print()
            print("✅ Memory system operational")
        else:
            print(f"❌ Error getting status: {status.get('error', 'Unknown error')}")
            return 1

    return 0


def handle_read(manager: SimpleMemoryManager, args) -> int:
    """Handle read command"""
    memory_data = manager.read_memory(section=args.section, limit=args.limit)

    if args.json:
        print(json.dumps(memory_data, indent=2))
    else:
        print(f"📖 Reading Memory (Issue #{memory_data['issue_number']})")
        print("=" * 50)

        if args.section:
            section_data = memory_data.get("filtered_section", [])
            print(f"Section: {args.section} ({len(section_data)} entries)")
            print()

            for entry in section_data:
                print(f"⏰ {entry.get('timestamp', 'Unknown time')}")
                print(f"👤 Agent: {entry.get('agent', 'Unknown')}")
                print(f"🔥 Priority: {entry.get('priority', 'medium')}")
                if entry.get("related_issues"):
                    print(
                        f"🔗 Related: {', '.join([f'#{i}' for i in entry['related_issues']])}"
                    )
                print()
                print(entry.get("content", "No content"))
                print("-" * 40)
        else:
            print(f"Total Comments: {memory_data['total_comments']}")
            print(f"Available Sections: {', '.join(memory_data['sections'].keys())}")
            print()
            print("Recent Updates:")
            for update in memory_data["all_updates"][-5:]:  # Show last 5
                print(
                    f"  [{update.get('section', 'unknown')}] {update.get('timestamp', 'unknown')} - {update.get('agent', 'unknown')}"
                )
                content_preview = update.get("content", "")[:100]
                if len(content_preview) == 100:
                    content_preview += "..."
                print(f"    {content_preview}")
                print()

    return 0


def handle_update(manager: SimpleMemoryManager, args) -> int:
    """Handle update command"""
    content = args.content

    # Read from stdin if content is '-'
    if content == "-":
        content = sys.stdin.read().strip()

    if not content:
        print("❌ Error: No content provided")
        return 1

    # Parse related issues/PRs from arguments
    related_issues = []
    related_prs = []

    if args.related:
        for ref in args.related.split(","):
            ref = ref.strip()
            if ref.startswith("#"):
                try:
                    related_issues.append(int(ref[1:]))
                except ValueError:
                    print(f"⚠️  Warning: Invalid issue reference '{ref}'")

    # Parse related files
    related_files = None
    if args.files:
        related_files = [f.strip() for f in args.files.split(",")]

    result = manager.update_memory(
        content=content,
        section=args.section,
        agent=args.agent,
        priority=args.priority,
        related_issues=related_issues or None,
        related_prs=related_prs or None,
        related_files=related_files,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print("✅ Memory updated successfully")
            print(f"Section: {result['section']}")
            print(f"Agent: {result['agent']}")
            print(f"Timestamp: {result['timestamp']}")
            if result.get("comment_url"):
                print(f"Comment URL: {result['comment_url']}")
        else:
            print(f"❌ Failed to update memory: {result.get('error', 'Unknown error')}")
            return 1

    return 0


def handle_search(manager: SimpleMemoryManager, args) -> int:
    """Handle search command"""
    results = manager.search_memory(args.query, section=args.section)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if results["success"]:
            print(f"🔍 Search Results for '{args.query}'")
            if args.section:
                print(f"Section Filter: {args.section}")
            print("=" * 50)

            if results["total_results"] == 0:
                print("No matching results found.")
            else:
                print(f"Found {results['total_results']} results:")
                print()

                for i, result in enumerate(results["results"], 1):
                    print(
                        f"{i}. [{result.get('section', 'unknown')}] {result.get('timestamp', 'unknown')}"
                    )
                    print(f"   Agent: {result.get('agent', 'unknown')}")
                    content_preview = result.get("content", "")[:150]
                    if len(content_preview) == 150:
                        content_preview += "..."
                    print(f"   {content_preview}")
                    print()
        else:
            print(f"❌ Search failed: {results.get('error', 'Unknown error')}")
            return 1

    return 0


def handle_cleanup(manager: SimpleMemoryManager, args) -> int:
    """Handle cleanup command"""
    result = manager.cleanup_old_memory(days_old=args.days, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print("🧹 Memory Cleanup")
            print("=" * 30)
            print(f"Mode: {'Dry Run' if result['dry_run'] else 'Live Run'}")
            print(f"Total Comments: {result['total_comments']}")
            print(f"Comments to Archive: {result['comments_to_archive']}")
            if result.get("note"):
                print(f"Note: {result['note']}")
        else:
            print(f"❌ Cleanup failed: {result.get('error', 'Unknown error')}")
            return 1

    return 0


def handle_lock_status(manager: SimpleMemoryManager, args) -> int:
    """Handle lock status command"""
    result = manager.check_lock_status()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print("🔒 Memory Issue Lock Status")
            print("=" * 40)
            print(f"Issue Number: #{result['issue_number']}")
            print(f"Locked: {'Yes' if result['locked'] else 'No'}")
            if result["locked"] and result.get("lock_reason"):
                print(f"Lock Reason: {result['lock_reason']}")
            if result["locked"]:
                print("\n✅ Memory is protected from unauthorized modifications")
                print("Only collaborators with write access can comment")
            else:
                print("\n⚠️  Memory is NOT locked - anyone can comment!")
                print("Consider locking for security")
        else:
            print(
                f"❌ Failed to check lock status: {result.get('error', 'Unknown error')}"
            )
            return 1

    return 0


def handle_unlock(manager: SimpleMemoryManager, args) -> int:
    """Handle unlock command"""
    if not args.confirm:
        print("⚠️  WARNING: Unlocking the memory issue reduces security!")
        print(
            "Non-collaborators will be able to add comments (potential memory poisoning)"
        )
        print("\nTo proceed, use: --confirm")
        return 1

    result = manager.unlock_memory_issue()

    if args.json:
        print(json.dumps({"success": result}, indent=2))
    else:
        if result:
            print("🔓 Memory issue unlocked")
            print("⚠️  WARNING: Non-collaborators can now comment on the memory issue")
        else:
            print("❌ Failed to unlock memory issue")
            return 1

    return 0


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Simple Memory Manager - GitHub Issues as Single Source of Truth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check memory status
  python simple_memory_cli.py status

  # Read all memory
  python simple_memory_cli.py read

  # Read specific section
  python simple_memory_cli.py read --section current-goals

  # Add memory update
  python simple_memory_cli.py update "New feature completed" --section completed-tasks --agent WorkflowManager --priority high

  # Add memory from stdin
  echo "Long memory content..." | python simple_memory_cli.py update - --section important-context --agent OrchestratorAgent

  # Search memory
  python simple_memory_cli.py search "performance improvement"

  # Search specific section
  python simple_memory_cli.py search "bug fix" --section completed-tasks

  # Check memory lock status
  python simple_memory_cli.py lock-status

  # Unlock memory (requires confirmation)
  python simple_memory_cli.py unlock --confirm
        """,
    )

    parser.add_argument(
        "--repo-path", help="Path to repository (default: current directory)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show memory system status")

    # Read command
    read_parser = subparsers.add_parser("read", help="Read memory content")
    read_parser.add_argument("--section", help="Read specific section only")
    read_parser.add_argument(
        "--limit", type=int, help="Limit number of entries returned"
    )

    # Update command
    update_parser = subparsers.add_parser("update", help="Add memory update")
    update_parser.add_argument(
        "content", help='Memory content (use "-" to read from stdin)'
    )
    update_parser.add_argument(
        "--section",
        required=True,
        choices=[
            "current-goals",
            "completed-tasks",
            "important-context",
            "next-steps",
            "reflections",
        ],
        help="Memory section",
    )
    update_parser.add_argument(
        "--agent", required=True, help="Agent name adding the memory"
    )
    update_parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        default="medium",
        help="Priority level",
    )
    update_parser.add_argument(
        "--related",
        help='Comma-separated list of related issues/PRs (e.g., "#123,#456")',
    )
    update_parser.add_argument("--files", help="Comma-separated list of related files")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search memory content")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--section", help="Search within specific section only")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Archive old memory entries")
    cleanup_parser.add_argument(
        "--days", type=int, default=30, help="Archive entries older than N days"
    )
    cleanup_parser.add_argument(
        "--dry-run", action="store_true", help="Preview what would be archived"
    )

    # Lock command
    subparsers.add_parser("lock-status", help="Check memory issue lock status")

    # Unlock command (with warning)
    unlock_parser = subparsers.add_parser(
        "unlock", help="Unlock memory issue (WARNING: reduces security)"
    )
    unlock_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm you want to unlock (allows non-collaborators to comment)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging
    setup_logging(args.verbose)

    try:
        # Initialize Simple Memory Manager
        manager = SimpleMemoryManager(args.repo_path)

        # Route to appropriate handler
        if args.command == "status":
            return handle_status(manager, args)
        elif args.command == "read":
            return handle_read(manager, args)
        elif args.command == "update":
            return handle_update(manager, args)
        elif args.command == "search":
            return handle_search(manager, args)
        elif args.command == "cleanup":
            return handle_cleanup(manager, args)
        elif args.command == "lock-status":
            return handle_lock_status(manager, args)
        elif args.command == "unlock":
            return handle_unlock(manager, args)
        else:
            print(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        if args.verbose:
            import traceback

            traceback.print_exc()
        else:
            print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
