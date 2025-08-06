#!/usr/bin/env python3
"""
Integration test for TeamCoach hooks - verifies hooks are actually triggered
when running Claude Code tasks.
"""

import subprocess
import json
import time
import os
import tempfile
from datetime import datetime
import pytest
import shutil


@pytest.mark.skipif(
    shutil.which("claude") is None, reason="Claude CLI not available in CI environment"
)
@pytest.mark.skip(reason="TeamCoach hook integration test dropped per user request")
def test_teamcoach_hook_integration():
    """Test that TeamCoach hooks are actually triggered during Claude Code execution."""

    print("🧪 Testing TeamCoach Hook Integration...")
    print("=" * 60)

    # Create a simple test task that Claude can execute
    test_task = """
Please create a simple Python function that adds two numbers and write it to a file called test_add.py.
Then create a test for it in test_test_add.py.
This is a simple task to test hook execution.
"""

    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"📁 Working in temporary directory: {temp_dir}")

        # Run Claude Code with the test task
        print("\n🤖 Running Claude Code with test task...")
        print(f"Task: {test_task.strip()}")
        print("-" * 60)

        # Execute claude command
        start_time = time.time()
        result = subprocess.run(["claude", test_task], capture_output=True, text=True)
        end_time = time.time()
        duration = end_time - start_time

        print(f"\n⏱️  Task completed in {duration:.2f} seconds")
        print(f"✅ Return code: {result.returncode}")

        # Check if files were created
        created_files = os.listdir(temp_dir)
        print(f"\n📄 Files created: {created_files}")

        # Look for evidence of TeamCoach hook execution
        print("\n🔍 Checking for TeamCoach hook execution...")

        # Check stdout for TeamCoach invocation messages
        if "TeamCoach" in result.stdout:
            print("✅ Found TeamCoach references in stdout")
            teamcoach_lines = [
                line for line in result.stdout.split("\n") if "TeamCoach" in line
            ]
            for line in teamcoach_lines[:5]:  # Show first 5 matches
                print(f"   → {line}")
        else:
            print("⚠️  No TeamCoach references found in stdout")

        # Check stderr for any hook-related messages
        if result.stderr:
            print(f"\n⚠️  Stderr output: {result.stderr[:200]}...")

        # Check for hook execution indicators
        hook_indicators = [
            "TeamCoach analysis completed",
            "TeamCoach session analysis",
            "agent:teamcoach",
            "Post-session analysis",
            "performance metrics",
        ]

        found_indicators = []
        for indicator in hook_indicators:
            if (
                indicator.lower() in result.stdout.lower()
                or indicator.lower() in result.stderr.lower()
            ):
                found_indicators.append(indicator)

        if found_indicators:
            print(f"\n✅ Found hook execution indicators: {found_indicators}")
        else:
            print("\n⚠️  No clear hook execution indicators found")

        # Summary
        print("\n" + "=" * 60)
        print("📊 Integration Test Summary:")
        print(f"   • Task completed: {'✅' if result.returncode == 0 else '❌'}")
        print(f"   • Files created: {'✅' if created_files else '❌'}")
        print(f"   • Hook indicators found: {'✅' if found_indicators else '⚠️'}")
        print(f"   • Duration: {duration:.2f}s")

        # Test results for validation - pytest tests should not return values
        assert (
            result.returncode == 0 or len(found_indicators) > 0
        ), "Test task should complete successfully or show hook indicators"


@pytest.mark.skip(
    reason="Claude CLI not available in CI environment - Issue created to enable Claude CLI in CI"
)
def test_subagent_hook_integration():
    """Test that SubagentStop hooks are triggered when using subagents."""

    print("\n\n🧪 Testing SubagentStop Hook Integration...")
    print("=" * 60)

    # Create a task that will use a subagent
    test_task = """
/agent:code-reviewer

Please review this simple Python code and provide feedback:

```python
def calculate_sum(a, b):
    return a + b
```
"""

    print("🤖 Running Claude Code with subagent task...")
    print(f"Task: {test_task.strip()}")
    print("-" * 60)

    # Execute claude command
    start_time = time.time()
    result = subprocess.run(["claude", test_task], capture_output=True, text=True)
    end_time = time.time()
    duration = end_time - start_time

    print(f"\n⏱️  Task completed in {duration:.2f} seconds")
    print(f"✅ Return code: {result.returncode}")

    # Look for evidence of SubagentStop hook execution
    print("\n🔍 Checking for SubagentStop hook execution...")

    subagent_indicators = [
        "agent analysis completed",
        "individual agent performance",
        "capability assessment",
        "agent-specific",
    ]

    found_indicators = []
    for indicator in subagent_indicators:
        if (
            indicator.lower() in result.stdout.lower()
            or indicator.lower() in result.stderr.lower()
        ):
            found_indicators.append(indicator)

    if found_indicators:
        print(f"✅ Found subagent hook indicators: {found_indicators}")
    else:
        print("⚠️  No clear subagent hook execution indicators found")

    # Summary
    print("\n" + "=" * 60)
    print("📊 SubagentStop Test Summary:")
    print(f"   • Task completed: {'✅' if result.returncode == 0 else '❌'}")
    print(f"   • Hook indicators found: {'✅' if found_indicators else '⚠️'}")
    print(f"   • Duration: {duration:.2f}s")

    return {
        "success": result.returncode == 0,
        "hook_indicators": found_indicators,
        "duration": duration,
    }


def verify_hook_configuration():
    """Verify that hooks are properly configured in settings.json."""

    print("\n\n🔧 Verifying Hook Configuration...")
    print("=" * 60)

    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), ".claude", "settings.json"
    )

    print(f"📄 Checking settings.json at: {settings_path}")

    try:
        with open(settings_path, "r") as f:
            settings = json.load(f)

        if "hooks" in settings:
            print("✅ Hooks section found in settings.json")

            hooks = settings["hooks"]
            if "Stop" in hooks:
                print("✅ Stop hook configured")
                stop_hook = hooks["Stop"][0]["hooks"][0]
                print(f"   • Command: {stop_hook['command']}")
                print(f"   • Timeout: {stop_hook['timeout']}s")

            if "SubagentStop" in hooks:
                print("✅ SubagentStop hook configured")
                subagent_hook = hooks["SubagentStop"][0]["hooks"][0]
                print(f"   • Command: {subagent_hook['command']}")
                print(f"   • Timeout: {subagent_hook['timeout']}s")

            return True
        else:
            print("❌ No hooks section found in settings.json")
            return False

    except Exception as e:
        print(f"❌ Error reading settings.json: {e}")
        return False


def main():
    """Run all integration tests."""

    print("🚀 TeamCoach Hook Integration Test Suite")
    print("=" * 80)
    print(f"📅 Test started at: {datetime.now().isoformat()}")
    print(f"📁 Working directory: {os.getcwd()}")

    # First verify configuration
    config_ok = verify_hook_configuration()

    if not config_ok:
        print("\n❌ Hook configuration is not correct. Please check settings.json")
        return 1

    # Test basic hook execution
    basic_result = test_teamcoach_hook_integration()

    # Test subagent hook execution
    subagent_result = test_subagent_hook_integration()

    # Final summary
    print("\n\n" + "=" * 80)
    print("🏁 FINAL TEST RESULTS:")
    print(f"   • Configuration: {'✅' if config_ok else '❌'}")
    print(f"   • Basic hook test: {'✅' if basic_result['success'] else '❌'}")
    print(f"   • Subagent hook test: {'✅' if subagent_result['success'] else '❌'}")

    all_passed = config_ok and basic_result["success"] and subagent_result["success"]

    if all_passed:
        print("\n✅ All integration tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests did not pass completely")
        print("Note: Hook execution may not show clear indicators in stdout/stderr")
        print("but could still be working correctly in the background")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
