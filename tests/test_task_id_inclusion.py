import sys
import os

#!/usr/bin/env python3
from ..shared.github_operations import GitHubOperations
from unittest.mock import Mock, patch, MagicMock
"""
Test script to verify task ID inclusion in GitHub operations.
"""

from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude.shared.github_operations import GitHubOperations

def test_task_id_formatting():
    """Test that task ID is properly formatted in GitHub operations."""

    # Generate a test task ID
    task_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}-abcd"

    # Create GitHubOperations instance with task ID
    github_ops = GitHubOperations(task_id=task_id)

    # Test the format_task_id_metadata method
    metadata = github_ops._format_task_id_metadata()

    # Verify the format
    expected = f"\n\n---\n**Task ID**: `{task_id}`"
    assert metadata == expected, f"Expected: {expected}, Got: {metadata}"

    print("✅ Task ID formatting test passed")
    print(f"   Task ID: {task_id}")
    print(f"   Formatted metadata: {metadata}")

    # Test with no task ID
    github_ops_no_id = GitHubOperations()
    metadata_no_id = github_ops_no_id._format_task_id_metadata()
    assert metadata_no_id == "", "Expected empty string when no task ID"

    print("✅ No task ID test passed")

    return True

def test_issue_creation_mock():
    """Mock test for issue creation with task ID."""

    task_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}-1234"
    github_ops = GitHubOperations(task_id=task_id)

    # Mock the body that would be sent
    original_body = "This is a test issue description"
    body_with_task_id = original_body + github_ops._format_task_id_metadata()

    # Verify task ID is included
    assert task_id in body_with_task_id, "Task ID not found in body"
    assert "**Task ID**:" in body_with_task_id, "Task ID label not found"

    print("✅ Issue creation mock test passed")
    print(f"   Original body: {original_body}")
    print(f"   Body with task ID: {body_with_task_id}")

    return True

def test_pr_creation_mock():
    """Mock test for PR creation with task ID."""

    task_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}-5678"
    github_ops = GitHubOperations(task_id=task_id)

    # Mock the body that would be sent
    original_body = "This PR implements feature X"
    body_with_task_id = original_body + github_ops._format_task_id_metadata()

    # Verify task ID is included
    assert task_id in body_with_task_id, "Task ID not found in PR body"
    assert "---" in body_with_task_id, "Separator not found"

    print("✅ PR creation mock test passed")
    print(f"   Body includes task ID: {task_id}")

    return True

def test_comment_mock():
    """Mock test for comment creation with task ID."""

    task_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}-9abc"
    github_ops = GitHubOperations(task_id=task_id)

    # Mock the comment that would be sent
    original_comment = "LGTM! Ready to merge."
    comment_with_task_id = original_comment + github_ops._format_task_id_metadata()

    # Verify task ID is included
    assert task_id in comment_with_task_id, "Task ID not found in comment"

    print("✅ Comment mock test passed")
    print(f"   Comment includes task ID: {task_id}")

    return True

def main():
    """Run all tests."""

    print("🧪 Testing Task ID Inclusion in GitHub Operations\n")

    tests = [
        ("Task ID Formatting", test_task_id_formatting),
        ("Issue Creation Mock", test_issue_creation_mock),
        ("PR Creation Mock", test_pr_creation_mock),
        ("Comment Mock", test_comment_mock),
    ]

    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        try:
            result = test_func()
            if not result:
                all_passed = False
                print(f"❌ {test_name} failed")
        except Exception as e:
            all_passed = False
            print(f"❌ {test_name} failed with error: {e}")

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed successfully!")
        print("\nTask ID inclusion is working correctly.")
        print("GitHub operations will now include task IDs for better traceability.")
    else:
        print("❌ Some tests failed. Please review the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
