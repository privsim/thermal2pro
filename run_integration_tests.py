#!/usr/bin/env python3
import unittest
import sys
import traceback

def run_tests():
    """Run integration tests with detailed error reporting."""
    try:
        print("\n=== Starting Integration Tests ===\n")
        
        # Import test module
        print("Importing test module...")
        from tests.test_integration import IntegrationTests
        
        # Create test suite
        print("Creating test suite...")
        suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTests)
        
        # Create test runner with buffer disabled
        print("Creating test runner...")
        runner = unittest.TextTestRunner(verbosity=2, buffer=False, stream=sys.stdout)
        
        # Run tests
        print("\nRunning tests...\n")
        result = runner.run(suite)
        
        # Print summary
        print("\n=== Test Summary ===")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        # Print failures and errors in detail
        if result.failures:
            print("\n=== Test Failures ===")
            for test, traceback in result.failures:
                print(f"\n{test}")
                print(traceback)
        
        if result.errors:
            print("\n=== Test Errors ===")
            for test, traceback in result.errors:
                print(f"\n{test}")
                print(traceback)
        
        print("\n=== Test Run Complete ===\n")
        return len(result.failures) + len(result.errors)
        
    except Exception as e:
        print("\n!!! Error running tests !!!")
        print(traceback.format_exc())
        return 1

if __name__ == '__main__':
    try:
        print("\nPython version:", sys.version)
        print("Platform:", sys.platform)
        print("Running from:", sys.executable)
        print()
        sys.exit(run_tests())
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print("\nUnexpected error:", e)
        print(traceback.format_exc())
        sys.exit(1)