#!/usr/bin/env python3
"""
Test Runner for Orchestrator Implementation

This script runs comprehensive tests for the orchestrator implementation,
validating all components and their integration.
"""

import sys
import unittest
from pathlib import Path

# Add orchestrator components to path
orchestrator_dir = Path(__file__).parent.parent
sys.path.insert(0, str(orchestrator_dir))

# Import test modules
from tests.test_orchestrator_integration import TestOrchestratorIntegration, TestOrchestratorPerformance
from tests.test_process_registry import TestProcessRegistry, TestProcessInfo


def run_all_tests():
    """Run all orchestrator tests"""
    print("🧪 Running Orchestrator Implementation Tests")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestOrchestratorIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestOrchestratorPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessInfo))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    # Print failure details
    if result is not None and result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"❌ {test}: {traceback}")

    if result is not None and result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"💥 {test}: {traceback}")

    # Overall result
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} TESTS FAILED")
        return 1


def run_specific_test(test_name):
    """Run a specific test class or method"""
    print(f"🧪 Running Specific Test: {test_name}")
    print("=" * 60)

    # Map test names to classes
    test_classes = {
        'integration': TestOrchestratorIntegration,
        'performance': TestOrchestratorPerformance,
        'registry': TestProcessRegistry,
        'process_info': TestProcessInfo,
    }

    if test_name in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_classes[test_name])
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1
    else:
        print(f"Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_classes.keys())}")
        return 1


def validate_environment():
    """Validate test environment setup"""
    print("🔍 Validating Test Environment")
    print("=" * 60)

    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

    # Check required modules
    required_modules = [
        'json', 'tempfile', 'unittest', 'pathlib', 'datetime',
        'threading', 'subprocess', 'logging'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}")

    # Check optional modules
    optional_modules = ['psutil']
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✅ {module} (optional)")
        except ImportError:
            print(f"⚠️  {module} (optional, some tests may be skipped)")

    # Check orchestrator components
    orchestrator_components = [
        'orchestrator_main', 'orchestrator_cli', 'process_registry'
    ]

    for component in orchestrator_components:
        try:
            __import__(component)
            print(f"✅ {component}")
        except ImportError as e:
            print(f"❌ {component}: {e}")
            missing_modules.append(component)

    if missing_modules:
        print(f"\n❌ Missing required modules: {', '.join(missing_modules)}")
        return 1
    else:
        print(f"\n✅ Environment validation passed!")
        return 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Orchestrator Test Runner")
    parser.add_argument("--test", help="Run specific test (integration, performance, registry, process_info)")
    parser.add_argument("--validate", action="store_true", help="Validate test environment")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    # Set up logging
    import logging
    if args is not None and args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Handle commands
    if args is not None and args.validate:
        return validate_environment()
    elif args is not None and args.test:
        return run_specific_test(args.test)
    else:
        return run_all_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
