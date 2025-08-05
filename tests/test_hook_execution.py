#!/usr/bin/env python3
"""
Direct test of TeamCoach hook script execution
"""

import subprocess
import json
import os


def test_hook_direct_execution():
    """Test that the hook scripts can be executed directly."""

    print("🧪 Testing Direct Hook Execution")
    print("=" * 60)

    # Test Stop hook
    stop_hook = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        ".claude",
        "hooks",
        "teamcoach-stop.py",
    )

    print(f"\n📄 Testing Stop Hook: {stop_hook}")
    print(f"   Exists: {os.path.exists(stop_hook)}")
    print(f"   Executable: {os.access(stop_hook, os.X_OK)}")

    # Run the hook with empty input
    try:
        result = subprocess.run(
            ["python", stop_hook],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10,
        )

        print(f"   Return code: {result.returncode}")

        if result.stdout:
            try:
                output = json.loads(result.stdout)
                print("   ✅ Valid JSON output")
                print(f"   Action: {output.get('action', 'N/A')}")
                print(f"   Message: {output.get('message', 'N/A')[:60]}...")
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON output: {result.stdout[:100]}")

        if result.stderr:
            print(f"   Stderr: {result.stderr[:100]}")

    except subprocess.TimeoutExpired:
        print("   ❌ Hook timed out")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test SubagentStop hook
    subagent_hook = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        ".claude",
        "hooks",
        "teamcoach-subagent-stop.py",
    )

    print(f"\n📄 Testing SubagentStop Hook: {subagent_hook}")
    print(f"   Exists: {os.path.exists(subagent_hook)}")
    print(f"   Executable: {os.access(subagent_hook, os.X_OK)}")

    # Run the hook with agent data
    agent_data = {"agent_name": "test-agent", "result": "success", "duration": 42}

    try:
        result = subprocess.run(
            ["python", subagent_hook],
            input=json.dumps(agent_data),
            capture_output=True,
            text=True,
            timeout=10,
        )

        print(f"   Return code: {result.returncode}")

        if result.stdout:
            try:
                output = json.loads(result.stdout)
                print("   ✅ Valid JSON output")
                print(f"   Action: {output.get('action', 'N/A')}")
                print(f"   Message: {output.get('message', 'N/A')[:60]}...")
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON output: {result.stdout[:100]}")

        if result.stderr:
            print(f"   Stderr: {result.stderr[:100]}")

    except subprocess.TimeoutExpired:
        print("   ❌ Hook timed out")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_claude_in_path():
    """Test if claude command is available in PATH."""

    print("\n\n🔍 Checking Claude Command Availability")
    print("=" * 60)

    try:
        result = subprocess.run(["which", "claude"], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Claude found at: {result.stdout.strip()}")
        else:
            print("❌ Claude command not found in PATH")

        # Try to get version
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"   Version: {result.stdout.strip()}")
        else:
            print(f"   Could not get version: {result.stderr.strip()}")

    except Exception as e:
        print(f"❌ Error checking claude command: {e}")


def test_hook_with_mock_claude():
    """Test hook with a mock claude command to see if it would invoke TeamCoach."""

    print("\n\n🧪 Testing Hook TeamCoach Invocation")
    print("=" * 60)

    # Create a mock claude script
    mock_claude = """#!/usr/bin/env python3
import sys
print(f"MOCK CLAUDE CALLED WITH: {sys.argv}")
if '/agent:teamcoach' in sys.argv:
    print("✅ TeamCoach agent would be invoked!")
sys.exit(0)
"""

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(mock_claude)
        mock_path = f.name

    os.chmod(mock_path, 0o755)

    # Modify PATH to use our mock
    original_path = os.environ.get("PATH", "")
    mock_dir = os.path.dirname(mock_path)
    os.environ["PATH"] = f"{mock_dir}:{original_path}"

    # Create symlink to mock as 'claude'
    claude_link = os.path.join(mock_dir, "claude")
    os.symlink(mock_path, claude_link)

    try:
        # Now run the stop hook
        stop_hook = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".claude",
            "hooks",
            "teamcoach-stop.py",
        )

        result = subprocess.run(
            ["python", stop_hook], input="{}", capture_output=True, text=True, timeout=5
        )

        print("Hook execution with mock claude:")
        print(f"   Return code: {result.returncode}")

        if (
            "TeamCoach agent would be invoked" in result.stdout
            or "TeamCoach agent would be invoked" in result.stderr
        ):
            print("   ✅ Hook would invoke TeamCoach!")
        else:
            print("   ⚠️  No clear indication TeamCoach would be invoked")

        if result.stdout:
            print(f"   Stdout preview: {result.stdout[:200]}")
        if result.stderr:
            print(f"   Stderr preview: {result.stderr[:200]}")

    finally:
        # Restore PATH
        os.environ["PATH"] = original_path
        # Clean up
        os.unlink(claude_link)
        os.unlink(mock_path)


if __name__ == "__main__":
    test_hook_direct_execution()
    test_claude_in_path()
    test_hook_with_mock_claude()
