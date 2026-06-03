#!/usr/bin/env bash
# Run Python unit tests with coverage reporting
set -euo pipefail

cd "$(dirname "$0")/.."

echo "============================================================"
echo "  MKMChat — Unit Test Suite + Coverage"
echo "============================================================"

mkdir -p data/output/audit

python -m pytest tests/ \
    --ignore=tests/e2e \
    --ignore=tests/js \
    -q \
    --cov=src \
    --cov-report=html:data/output/audit/coverage_html \
    --cov-report=xml:data/output/audit/coverage.xml \
    --cov-report=term-missing \
    --junitxml=data/output/audit/test_results.xml \
    "$@"

echo ""
echo "Coverage HTML report: data/output/audit/coverage_html/index.html"
echo "Coverage XML report:  data/output/audit/coverage.xml"
echo "JUnit XML report:     data/output/audit/test_results.xml"
