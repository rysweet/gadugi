#!/usr/bin/env python3
"""
Cleanup script for removing the old Memory.md sync system

This script safely removes the old memory system components after
confirming the new hierarchical memory system is working correctly.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json


def create_cleanup_report():
    """Create a report of what will be removed"""
    repo_path = Path(os.getcwd())

    cleanup_targets = {
        "directories": [
            repo_path / ".github" / "memory-manager",
        ],
        "files": [
            repo_path / ".github" / "Memory.md",
            repo_path / ".github" / "memory-manager-config.yaml",
        ],
        "backup_created": [repo_path / ".github" / "Memory.md.backup"],
    }

    report = {
        "timestamp": datetime.now().isoformat(),
        "old_system_components": {
            "directories": [],
            "files": [],
            "total_size_bytes": 0,
        },
        "new_system_status": {
            "memory_directory_exists": (repo_path / ".memory").exists(),
            "utils_directory_exists": (repo_path / ".memory_utils").exists(),
            "memory_files_count": 0,
        },
    }

    # Check old system components
    for dir_path in cleanup_targets["directories"]:
        if dir_path.exists():
            size = sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file())
            report["old_system_components"]["directories"].append(
                {
                    "path": str(dir_path),
                    "exists": True,
                    "size_bytes": size,
                    "file_count": len(list(dir_path.rglob("*"))),
                }
            )
            report["old_system_components"]["total_size_bytes"] += size

    for file_path in cleanup_targets["files"]:
        if file_path.exists():
            size = file_path.stat().st_size
            report["old_system_components"]["files"].append(
                {"path": str(file_path), "exists": True, "size_bytes": size}
            )
            report["old_system_components"]["total_size_bytes"] += size

    # Check new system status
    memory_dir = repo_path / ".memory"
    if memory_dir.exists():
        memory_files = list(memory_dir.rglob("*.md"))
        report["new_system_status"]["memory_files_count"] = len(memory_files)

    return report


def perform_cleanup(dry_run=False):
    """Remove old memory system components"""
    repo_path = Path(os.getcwd())

    cleanup_targets = {
        "directories": [
            repo_path / ".github" / "memory-manager",
        ],
        "files": [
            repo_path / ".github" / "Memory.md",
        ],
    }

    removed = {"directories": [], "files": [], "errors": []}

    print(f"{'DRY RUN: ' if dry_run else ''}Starting cleanup of old memory system...")

    # Remove directories
    for dir_path in cleanup_targets["directories"]:
        if dir_path.exists():
            try:
                if not dry_run:
                    shutil.rmtree(dir_path)
                removed["directories"].append(str(dir_path))
                print(
                    f"  {'Would remove' if dry_run else 'Removed'} directory: {dir_path}"
                )
            except Exception as e:
                removed["errors"].append(f"Failed to remove {dir_path}: {e}")
                print(f"  ERROR removing {dir_path}: {e}")

    # Remove files
    for file_path in cleanup_targets["files"]:
        if file_path.exists():
            try:
                if not dry_run:
                    file_path.unlink()
                removed["files"].append(str(file_path))
                print(f"  {'Would remove' if dry_run else 'Removed'} file: {file_path}")
            except Exception as e:
                removed["errors"].append(f"Failed to remove {file_path}: {e}")
                print(f"  ERROR removing {file_path}: {e}")

    return removed


def main():
    """Main cleanup function"""
    import argparse

    parser = argparse.ArgumentParser(description="Cleanup old Memory.md sync system")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without removing",
    )
    parser.add_argument(
        "--report-only", action="store_true", help="Generate report without cleanup"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Automatically confirm cleanup"
    )
    args = parser.parse_args()

    # Generate report
    report = create_cleanup_report()

    if args.report_only:
        print("Cleanup Report:")
        print(json.dumps(report, indent=2))
        return

    # Show what will be removed
    print("Old Memory System Cleanup Report")
    print("=" * 50)
    print(
        f"Old system size: {report['old_system_components']['total_size_bytes'] / 1024:.1f} KB"
    )
    print(
        f"New system status: {report['new_system_status']['memory_files_count']} memory files"
    )
    print()

    if (
        report["old_system_components"]["directories"]
        or report["old_system_components"]["files"]
    ):
        print("Components to remove:")
        for dir_info in report["old_system_components"]["directories"]:
            if dir_info["exists"]:
                print(
                    f"  Directory: {dir_info['path']} ({dir_info['file_count']} files)"
                )
        for file_info in report["old_system_components"]["files"]:
            if file_info["exists"]:
                print(
                    f"  File: {file_info['path']} ({file_info['size_bytes'] / 1024:.1f} KB)"
                )
        print()

        # Perform cleanup
        if not args.dry_run and not args.yes:
            response = input("Proceed with cleanup? (yes/no): ")
            if response.lower() != "yes":
                print("Cleanup cancelled.")
                return

        cleanup_result = perform_cleanup(dry_run=args.dry_run)

        print()
        print("Cleanup Summary:")
        print(f"  Removed {len(cleanup_result['directories'])} directories")
        print(f"  Removed {len(cleanup_result['files'])} files")
        if cleanup_result["errors"]:
            print(f"  Errors: {len(cleanup_result['errors'])}")
            for error in cleanup_result["errors"]:
                print(f"    - {error}")

        # Save cleanup report
        report_path = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report["cleanup_result"] = cleanup_result
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")
    else:
        print("No old system components found to remove.")


if __name__ == "__main__":
    main()
