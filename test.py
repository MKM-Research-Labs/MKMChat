#!/usr/bin/env python3
# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
MKM Research Test Suite Controller
===================================

Main entry point for running all tests before starting the application.
Run this file to validate that all routes and services are working correctly.

Usage:
    python test.py              # Run Python tests, then JavaScript tests
    python test.py --quick      # Run quick smoke tests only
    python test.py --verbose    # Run with verbose output
    python test.py --module routes  # Run specific test module
    python test.py --no-log     # Don't save output to log file
    python test.py --js         # Run JavaScript tests only
    python test.py --no-js      # Skip JavaScript tests
    python test.py --all        # Run both Python and JavaScript tests
"""

import sys
import os
import argparse
import unittest
import time
import io
import subprocess
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Results directory
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "results")


class TeeOutput:
    """Write to both stdout and a file simultaneously."""

    def __init__(self, file_path):
        self.terminal = sys.stdout
        self.log_file = open(file_path, 'w', encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

    def close(self):
        self.log_file.close()


def ensure_results_dir():
    """Ensure the results directory exists."""
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    return RESULTS_DIR


def discover_tests(test_dir="tests", pattern="test_*.py"):
    """Discover all test modules in the tests directory."""
    # Get absolute path to test directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_path = os.path.join(base_dir, test_dir)

    # Check if test directory exists
    if not os.path.isdir(test_path):
        print(f"Warning: Test directory '{test_path}' not found")
        return unittest.TestSuite()

    loader = unittest.TestLoader()
    suite = loader.discover(test_path, pattern=pattern, top_level_dir=base_dir)
    return suite


def run_tests(verbosity=2, pattern="test_*.py", failfast=False):
    """
    Run the test suite.

    Args:
        verbosity: 0=quiet, 1=normal, 2=verbose
        pattern: Pattern to match test files
        failfast: Stop on first failure

    Returns:
        bool: True if all tests passed, False otherwise
    """
    print("=" * 70)
    print("MKM RESEARCH TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Pattern: {pattern}")
    print("=" * 70)

    # Discover and run tests
    suite = discover_tests(pattern=pattern)

    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=failfast
    )

    start_time = time.time()
    result = runner.run(suite)
    elapsed_time = time.time() - start_time

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Time elapsed: {elapsed_time:.2f}s")
    print("=" * 70)

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


def run_quick_tests():
    """Run quick smoke tests only."""
    print("Running quick smoke tests...")
    return run_tests(pattern="test_smoke*.py")


def run_module_tests(module_name):
    """Run tests for a specific module."""
    pattern = f"test_{module_name}*.py"
    print(f"Running tests matching: {pattern}")
    return run_tests(pattern=pattern)


def run_javascript_tests(verbose=False):
    """
    Run JavaScript tests using Jest via npm.

    Args:
        verbose: Whether to show full test output

    Returns:
        bool: True if all tests passed, False otherwise
    """
    print("\n" + "=" * 70)
    print("JAVASCRIPT TEST SUITE (Jest)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Check if node_modules exists (in tests/js directory)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    js_test_dir = os.path.join(base_dir, "tests", "js")
    node_modules = os.path.join(js_test_dir, "node_modules")
    package_json = os.path.join(js_test_dir, "package.json")

    if not os.path.exists(package_json):
        print("⚠️  No package.json found - JavaScript tests not configured")
        return True  # Don't fail if JS tests aren't set up

    if not os.path.exists(node_modules):
        print("⚠️  node_modules not found. Running npm install...")
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=js_test_dir,
                check=True,
                capture_output=not verbose
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ npm install failed: {e}")
            return False
        except FileNotFoundError:
            print("❌ npm not found. Please install Node.js to run JavaScript tests.")
            return True  # Don't fail the whole suite

    # Run Jest tests
    start_time = time.time()
    try:
        cmd = ["npm", "test"]
        if not verbose:
            cmd.extend(["--", "--silent"])

        result = subprocess.run(
            cmd,
            cwd=js_test_dir,
            capture_output=True,
            text=True
        )

        elapsed_time = time.time() - start_time

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr and verbose:
            print(result.stderr)

        # Parse results from output
        output = result.stdout + result.stderr

        # Extract test counts from Jest output
        tests_passed = 0
        tests_failed = 0
        test_suites = 0

        for line in output.split('\n'):
            if 'Tests:' in line:
                # Parse "Tests: 112 passed, 112 total"
                if 'passed' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed,':
                            tests_passed = int(parts[i-1])
                        elif part == 'failed,':
                            tests_failed = int(parts[i-1])
            elif 'Test Suites:' in line:
                # Parse "Test Suites: 13 passed, 13 total"
                if 'passed' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed,':
                            test_suites = int(parts[i-1])

        print("\n" + "-" * 70)
        print("JAVASCRIPT TEST SUMMARY")
        print("-" * 70)
        print(f"Test Suites: {test_suites}")
        print(f"Tests passed: {tests_passed}")
        print(f"Tests failed: {tests_failed}")
        print(f"Time elapsed: {elapsed_time:.2f}s")
        print("-" * 70)

        if result.returncode == 0:
            print("✅ ALL JAVASCRIPT TESTS PASSED")
            return True
        else:
            print("❌ SOME JAVASCRIPT TESTS FAILED")
            return False

    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js to run JavaScript tests.")
        return True  # Don't fail if npm isn't available
    except Exception as e:
        print(f"❌ Error running JavaScript tests: {e}")
        return False


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MKM Research Test Suite Controller"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Run quick smoke tests only"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run with verbose output"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run with minimal output"
    )
    parser.add_argument(
        "--module", "-m",
        type=str,
        help="Run tests for a specific module (e.g., routes, services, config)"
    )
    parser.add_argument(
        "--failfast", "-f",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--start-app",
        action="store_true",
        help="Start the application after tests pass"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for the application (used with --start-app)"
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Don't save output to log file"
    )
    parser.add_argument(
        "--js", "--javascript",
        action="store_true",
        help="Run JavaScript tests only"
    )
    parser.add_argument(
        "--no-js",
        action="store_true",
        help="Skip JavaScript tests"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run both Python and JavaScript tests"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    tee = None
    log_file_path = None

    if not args.no_log:
        ensure_results_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = args.module if args.module else "all"
        log_file_path = os.path.join(RESULTS_DIR, f"test_run_{module_name}_{timestamp}.log")
        tee = TeeOutput(log_file_path)
        sys.stdout = tee
        print(f"[LOG] Output being saved to: {log_file_path}\n")

    try:
        # Determine verbosity
        verbosity = 2  # default verbose
        if args.quiet:
            verbosity = 0
        elif args.verbose:
            verbosity = 2

        # Run appropriate tests
        if args.js:
            # JavaScript tests only
            success = run_javascript_tests(verbose=args.verbose)
        elif args.quick:
            success = run_quick_tests()
        elif args.module:
            success = run_module_tests(args.module)
        elif args.all:
            # Run both Python and JavaScript tests
            python_success = run_tests(
                verbosity=verbosity,
                failfast=args.failfast
            )
            js_success = run_javascript_tests(verbose=args.verbose)
            success = python_success and js_success
        else:
            # Default: run Python tests, then JS tests unless --no-js
            success = run_tests(
                verbosity=verbosity,
                failfast=args.failfast
            )
            if not args.no_js and success:
                js_success = run_javascript_tests(verbose=args.verbose)
                success = success and js_success

        if log_file_path:
            print(f"\n[LOG] Test output saved to: {log_file_path}")

        # Optionally start the application
        if success and args.start_app:
            print("\n" + "=" * 70)
            print("STARTING APPLICATION")
            print("=" * 70)
            from src.app import DocumentQAApp
            app = DocumentQAApp()
            app.run(port=args.port)

        return 0 if success else 1

    finally:
        # Restore stdout and close log file
        if tee:
            sys.stdout = tee.terminal
            tee.close()


if __name__ == "__main__":
    sys.exit(main())
