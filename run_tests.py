#!/usr/bin/env python3
import pytest
import sys

def main():
    """Run integration tests with detailed output."""
    print("Starting integration tests...")
    
    # Run tests with output capturing disabled
    result = pytest.main([
        "tests/test_integration.py",
        "-v",
        "-s",
        "--tb=short",
        "--show-capture=all"
    ])
    
    print(f"\nTest run completed with exit code: {result}")
    return result

if __name__ == "__main__":
    sys.exit(main())