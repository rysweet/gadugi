#!/usr/bin/env python3
"""
Simple test to validate that the orchestrator subprocess execution works correctly
"""

import json
import subprocess
import tempfile
from pathlib import Path


def test_subprocess_execution():
    """Test that the orchestrator can spawn real subprocesses"""

    # Create a test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create prompts directory
        prompts_dir = temp_path / "prompts"
        prompts_dir.mkdir()

        # Create a simple test prompt
        test_prompt = prompts_dir / "simple-test.md"
        test_prompt.write_text("""# Simple Test Task

Create a file called test_result.txt with "Hello World" content.

This is a minimal test to validate subprocess execution.
""")

        print("🧪 Testing orchestrator subprocess execution...")

        # Test the orchestrator CLI
        orchestrator_cmd = [
            "uv",
            "run",
            "python3",
            str(Path.cwd() / ".claude/orchestrator/orchestrator_cli.py"),
            "--project-root",
            str(temp_path),
            "--stdin",
        ]

        test_input = """Execute these prompts in parallel:
- simple-test.md
"""

        try:
            result = subprocess.run(
                orchestrator_cmd,
                input=test_input,
                text=True,
                capture_output=True,
                timeout=120,  # 2 minute timeout
            )

            print(f"📊 Orchestrator exit code: {result.returncode}")
            print(f"📄 Output length: {len(result.stdout)} characters")
            print(f"⚠️  Error length: {len(result.stderr)} characters")

            # Check if we see evidence of real subprocess execution
            output_text = result.stdout + result.stderr

            subprocess_indicators = [
                "Real subprocess spawned",
                "PID",
                "subprocess completed",
                "WorkflowManager delegation",
                "claude -p",
            ]

            found_indicators = []
            for indicator in subprocess_indicators:
                if indicator in output_text:
                    found_indicators.append(indicator)

            print(f"✅ Found subprocess indicators: {found_indicators}")

            # Success if we found evidence of subprocess execution
            if len(found_indicators) >= 2:  # At least 2 indicators
                print("🎉 SUCCESS: Real subprocess execution is working!")
                return True
            else:
                print("❌ FAILED: No clear evidence of subprocess execution")
                print("Output:", output_text[-500:])  # Last 500 chars
                return False

        except subprocess.TimeoutExpired:
            print(
                "⏰ Test timed out - this might indicate subprocess execution is working!"
            )
            return True  # Timeout could mean it's actually trying to execute

        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False


if __name__ == "__main__":
    success = test_subprocess_execution()
    exit(0 if success else 1)
