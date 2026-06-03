#!/usr/bin/env bash
# Run Playwright E2E tests
set -euo pipefail

cd "$(dirname "$0")/.."

echo "============================================================"
echo "  MKMChat — E2E Test Suite (Playwright)"
echo "============================================================"

# Install browser if needed
python -m playwright install chromium 2>/dev/null || true

mkdir -p data/output/audit

python -m pytest tests/e2e/ \
    -q \
    --junitxml=data/output/audit/e2e_results.xml \
    "$@"

echo ""
echo "E2E JUnit XML report: data/output/audit/e2e_results.xml"
