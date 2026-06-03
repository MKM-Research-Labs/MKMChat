# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""XML parsers for JUnit test results and coverage reports."""

import os
import xml.etree.ElementTree as ET
from typing import Dict, Any


def load_junit_xml(path: str) -> Dict[str, Any]:
    """Parse JUnit XML and extract test counts."""
    if not os.path.exists(path):
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "time": 0, "suites": []}

    tree = ET.parse(path)
    root = tree.getroot()

    # Handle both <testsuites> and <testsuite> root elements
    if root.tag == "testsuites":
        suites = list(root)
    else:
        suites = [root]

    total = 0
    failures = 0
    skipped = 0
    errors = 0
    time_total = 0.0
    suite_details = []

    for suite in suites:
        s_tests = int(suite.get("tests", 0))
        s_failures = int(suite.get("failures", 0))
        s_errors = int(suite.get("errors", 0))
        s_skipped = int(suite.get("skipped", 0))
        s_time = float(suite.get("time", 0))
        s_name = suite.get("name", "unknown")

        total += s_tests
        failures += s_failures
        errors += s_errors
        skipped += s_skipped
        time_total += s_time

        suite_details.append({
            "name": s_name,
            "total": s_tests,
            "passed": s_tests - s_failures - s_errors - s_skipped,
            "failed": s_failures + s_errors,
            "skipped": s_skipped,
        })

    return {
        "total": total,
        "passed": total - failures - errors - skipped,
        "failed": failures + errors,
        "skipped": skipped,
        "time": round(time_total, 1),
        "suites": suite_details,
    }


def load_coverage_xml(path: str) -> Dict[str, Any]:
    """Parse coverage.xml and extract per-package coverage."""
    if not os.path.exists(path):
        return {"line_rate": 0, "lines_valid": 0, "lines_covered": 0, "packages": []}

    tree = ET.parse(path)
    root = tree.getroot()

    line_rate = float(root.get("line-rate", 0)) * 100
    lines_valid = int(root.get("lines-valid", 0))
    lines_covered = int(root.get("lines-covered", 0))

    packages = []
    for pkg in root.findall(".//package"):
        pkg_name = pkg.get("name", "unknown")
        pkg_rate = float(pkg.get("line-rate", 0)) * 100
        pkg_lines = 0
        pkg_covered = 0
        for cls in pkg.findall(".//class"):
            for line in cls.findall("lines/line"):
                pkg_lines += 1
                if int(line.get("hits", 0)) > 0:
                    pkg_covered += 1

        packages.append({
            "name": pkg_name,
            "coverage": round(pkg_rate, 1),
            "lines_valid": pkg_lines,
            "lines_covered": pkg_covered,
            "gap": pkg_lines - pkg_covered,
        })

    packages.sort(key=lambda x: x["coverage"])

    return {
        "line_rate": round(line_rate, 2),
        "lines_valid": lines_valid,
        "lines_covered": lines_covered,
        "packages": packages,
    }
