#!/usr/bin/env python3
"""
Test runner for OrchestratorAgent components

Runs all test suites and generates a comprehensive test report.
"""

import sys
import time
import unittest
from io import StringIO
from pathlib import Path

# Add components to path
sys.path.insert(0, str(Path(__file__).parent.parent / "components"))


def run_test_suite():
    """Run all OrchestratorAgent test suites"""
    print("🧪 Running OrchestratorAgent Test Suite")
    print("=" * 50)

    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent

    # Load all test modules
    suite = loader.discover(str(start_dir), pattern="test_*.py")

    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream, verbosity=2, buffer=True, failfast=False
    )

    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()

    # Print results
    output = stream.getvalue()
    print(output)

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, "skipped") else 0
    successful = total_tests - failures - errors - skipped

    print(f"Total tests:     {total_tests}")
    print(f"Successful:      {successful}")
    print(f"Failures:        {failures}")
    print(f"Errors:          {errors}")
    print(f"Skipped:         {skipped}")
    print(f"Execution time:  {end_time - start_time:.2f} seconds")

    if failures > 0:
        print("\n❌ Test Failures:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace.split('AssertionError:')[-1].strip()}")

    if errors > 0:
        print("\n💥 Test Errors:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace.split('Error:')[-1].strip()}")

    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
    print(f"\n✅ Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 Excellent test coverage!")
    elif success_rate >= 80:
        print("✅ Good test coverage")
    elif success_rate >= 70:
        print("⚠️  Acceptable test coverage, room for improvement")
    else:
        print("❌ Low test coverage, needs attention")

    return result.wasSuccessful()


def main():
    """Main entry point"""
    try:
        success = run_test_suite()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
