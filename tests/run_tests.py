#!/usr/bin/env python3
"""
QuickStart Test Runner for SwasthyaAI Validation Suite

Run this file to verify all validation fixes are working correctly.
"""

import subprocess
import sys
import os

def run_test_suite():
    """Run the comprehensive validation test suite"""
    print("\n" + "="*70)
    print("RUNNING SWASTHYAAI REGULATOR - VALIDATION TEST SUITE")
    print("="*70 + "\n")
    
    test_file = os.path.join(os.path.dirname(__file__), "test_validation_fixes.py")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=os.path.dirname(__file__),
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_test_suite()
    
    print("\n" + "="*70)
    if success:
        print("[SUCCESS] All validation fixes verified!")
        print("="*70)
        print("\nThe following have been fixed:")
        print("  1. Project reorganized (tests/, docs/, clean root)")
        print("  2. ADR validation field mapping working")
        print("  3. MD-14 flexible date format support")
        print("  4. MD-14 flexible enum matching (case-insensitive)")
        print("  5. All 10 validation tests passing")
        sys.exit(0)
    else:
        print("[FAILURE] Some tests failed")
        print("="*70)
        print("\nPlease check the output above for details.")
        sys.exit(1)
