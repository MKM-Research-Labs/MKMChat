#!/usr/bin/env bash
# Run all test suites: unit, E2E, and JavaScript
set -euo pipefail

cd "$(dirname "$0")/.."

PASS=0
FAIL=0

echo "============================================================"
echo "  MKMChat — Full Test Suite"
echo "============================================================"
echo ""

# --- Unit Tests ---
echo ">>> Running Python unit tests..."
if bash scripts/run_tests.sh; then
    echo "  PASS: Unit tests"
    ((PASS++))
else
    echo "  FAIL: Unit tests"
    ((FAIL++))
fi
echo ""

# --- E2E Tests ---
echo ">>> Running E2E tests..."
if bash scripts/run_e2e.sh; then
    echo "  PASS: E2E tests"
    ((PASS++))
else
    echo "  FAIL: E2E tests"
    ((FAIL++))
fi
echo ""

# --- JavaScript Tests ---
echo ">>> Running JavaScript tests..."
if cd tests/js && npx jest --coverage 2>/dev/null; then
    echo "  PASS: JavaScript tests"
    ((PASS++))
else
    echo "  FAIL: JavaScript tests"
    ((FAIL++))
fi
cd ../..
echo ""

# --- Summary ---
echo "============================================================"
echo "  RESULTS: $PASS passed, $FAIL failed"
echo "============================================================"
echo ""
echo "Reports:"
echo "  Coverage HTML:  data/output/audit/coverage_html/index.html"
echo "  Coverage XML:   data/output/audit/coverage.xml"
echo "  Unit JUnit:     data/output/audit/test_results.xml"
echo "  E2E JUnit:      data/output/audit/e2e_results.xml"

[ "$FAIL" -eq 0 ] || exit 1
