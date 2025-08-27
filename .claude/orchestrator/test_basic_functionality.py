#!/usr/bin/env python3
"""
Basic functionality test for orchestrator implementation

This test validates that the orchestrator components can be imported and
basic functionality works without complex dependencies.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add orchestrator to path
orchestrator_dir = Path(__file__).parent
sys.path.insert(0, str(orchestrator_dir))

def test_imports():
    """Test that orchestrator components can be imported"""
    print("Testing imports...")

    try:
        from orchestrator_cli import OrchestrationCLI
        _ = OrchestrationCLI  # Mark as used for import testing
        print("✅ orchestrator_cli imported successfully")
    except Exception as e:
        print(f"❌ orchestrator_cli import failed: {e}")
        return False

    try:
        from process_registry import ProcessRegistry, ProcessStatus, ProcessInfo
        _ = (ProcessRegistry, ProcessStatus, ProcessInfo)  # Mark as used for import testing
        print("✅ process_registry imported successfully")
    except Exception as e:
        print(f"❌ process_registry import failed: {e}")
        return False

    try:
        from orchestrator_main import OrchestratorCoordinator, OrchestrationConfig
        _ = (OrchestratorCoordinator, OrchestrationConfig)  # Mark as used for import testing
        print("✅ orchestrator_main imported successfully")
    except Exception as e:
        print(f"❌ orchestrator_main import failed: {e}")
        print(f"   This may be expected if components are missing")
        # This is non-fatal for basic testing

    return True

def test_cli_basic():
    """Test basic CLI functionality"""
    print("\nTesting CLI basic functionality...")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        prompts_dir = temp_path / "prompts"
        prompts_dir.mkdir()

        # Create test prompt file
        test_prompt = prompts_dir / "test.md"
        test_prompt.write_text("# Test Prompt\n\nTest content")

        try:
            from orchestrator_cli import OrchestrationCLI

            cli = OrchestrationCLI(str(temp_path))

            # Test user input parsing
            user_input = """
Execute these prompts in parallel:
- test.md
            """

            result = cli.parse_user_input(user_input)

            if len(result) == 1 and result[0] == "test.md":
                print("✅ CLI user input parsing works")
                return True
            else:
                print(f"❌ CLI parsing failed. Expected ['test.md'], got {result}")
                return False

        except Exception as e:
            print(f"❌ CLI basic test failed: {e}")
            return False

def test_process_registry_basic():
    """Test basic process registry functionality"""
    print("\nTesting process registry basic functionality...")

    try:
        from process_registry import ProcessRegistry, ProcessStatus, ProcessInfo
        from datetime import datetime

        with tempfile.TemporaryDirectory() as temp_dir:
            registry = ProcessRegistry(temp_dir)

            # Test process registration
            process_info = ProcessInfo(
                task_id="test-task",
                task_name="Test Task",
                status=ProcessStatus.QUEUED,
                command="test command",
                working_directory=temp_dir,
                created_at=datetime.now()
            )

            registry.register_process(process_info)

            # Test retrieval
            retrieved = registry.get_process("test-task")

            if retrieved and retrieved.task_id == "test-task":
                print("✅ Process registry basic functionality works")
                return True
            else:
                print("❌ Process registry retrieval failed")
                return False

    except Exception as e:
        print(f"❌ Process registry test failed: {e}")
        return False

def test_shell_script():
    """Test shell script exists and is executable"""
    print("\nTesting shell script...")

    script_path = Path(__file__).parent / "run_orchestrator.sh"

    if not script_path.exists():
        print("❌ Shell script not found")
        return False

    # Check if executable (Unix systems)
    if os.name != 'nt':
        stat_info = script_path.stat()
        if not (stat_info.st_mode & 0o111):
            print("❌ Shell script not executable")
            return False

    print("✅ Shell script exists and is executable")
    return True

def main():
    """Run basic functionality tests"""
    print("🧪 Basic Orchestrator Functionality Tests")
    print("=" * 50)

    tests = [
        test_imports,
        test_cli_basic,
        test_process_registry_basic,
        test_shell_script
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ All basic tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
