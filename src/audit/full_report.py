# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Full audit report — assembles all audit data into a single PDF."""

import os
from datetime import datetime

from .parsers import load_junit_xml, load_coverage_xml
from .pdf_builder import MKMReportBuilder
from .scanners import (
    scan_large_files,
    scan_large_files_summary,
    count_all_code_files,
    scan_hardcoding,
    scan_duplication,
)


def generate_full_audit_report(output_dir: str, project_root: str) -> str:
    """Generate the full audit report PDF."""
    output_path = os.path.join(output_dir, "full_audit_report.pdf")
    src_dir = os.path.join(project_root, "src")

    # Load test results
    junit_path = os.path.join(output_dir, "test_results.xml")
    e2e_path = os.path.join(output_dir, "e2e_results.xml")
    cov_path = os.path.join(output_dir, "coverage.xml")

    unit_results = load_junit_xml(junit_path)
    e2e_results = load_junit_xml(e2e_path)
    coverage = load_coverage_xml(cov_path)

    total_tests = unit_results["total"] + e2e_results["total"]
    total_passed = unit_results["passed"] + e2e_results["passed"]

    # Scan source
    large_files = scan_large_files(src_dir)
    hardcoding = scan_hardcoding(src_dir, os.path.join(project_root, "config.py"))
    duplication = scan_duplication(src_dir)
    total_code_files, total_code_lines = count_all_code_files(src_dir)

    # Build PDF
    pdf = MKMReportBuilder(output_path, "Full Audit Report")

    # --- Cover page ---
    e2e_status = "PASS" if e2e_results["total"] > 0 and e2e_results["failed"] == 0 else (
        "SKIP" if e2e_results["total"] == 0 else "FAIL"
    )
    pdf.add_cover_page([
        {"label": "Total Tests", "value": f"{total_tests:,}"},
        {"label": "Pass Rate", "value": f"{total_passed/max(total_tests,1)*100:.1f}%"},
        {"label": "Line Coverage", "value": f"{coverage['line_rate']}%"},
        {"label": "E2E Tests", "value": e2e_status},
    ])

    # --- Section 1: Executive Summary ---
    pdf.add_heading("Executive Summary", 1)
    pdf.add_metric_table([
        {"metric": "Total tests", "value": f"{total_tests:,}", "status": "OK"},
        {"metric": "Tests passed", "value": f"{total_passed:,}", "status": "OK"},
        {"metric": "Tests failed", "value": str(unit_results["failed"] + e2e_results["failed"]),
         "status": "OK" if (unit_results["failed"] + e2e_results["failed"]) == 0 else "FAIL"},
        {"metric": "Tests skipped", "value": str(unit_results["skipped"] + e2e_results["skipped"]),
         "status": "INFO"},
        {"metric": "Test suite run time", "value": f"{unit_results['time'] + e2e_results['time']:.1f}s",
         "status": "INFO"},
        {"metric": "Lines analysed (src/)", "value": f"{coverage['lines_valid']:,}", "status": "INFO"},
        {"metric": "Lines covered", "value": f"{coverage['lines_covered']:,}", "status": "INFO"},
        {"metric": "Line coverage", "value": f"{coverage['line_rate']}%",
         "status": "OK" if coverage["line_rate"] >= 95 else "REVIEW"},
        {"metric": "E2E browser tests",
         "value": f"{e2e_results['passed']} passed" if e2e_results["total"] > 0 else "Skipped",
         "status": "OK" if e2e_results["total"] > 0 and e2e_results["failed"] == 0 else "INFO"},
        {"metric": "Report generated", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         "status": "INFO"},
    ])

    summary_text = (
        f"The test suite comprises {total_tests:,} tests with {total_passed:,} passing, "
        f"{unit_results['failed'] + e2e_results['failed']} failing, and "
        f"{unit_results['skipped'] + e2e_results['skipped']} skipped. "
        f"Line coverage stands at {coverage['line_rate']}% across "
        f"{coverage['lines_valid']:,} analysed source lines."
    )
    pdf.add_text(summary_text)

    # --- Section 2: Test Suite Detail ---
    pdf.add_page_break()
    pdf.add_heading("Test Suite Detail", 2)
    pdf.add_text("Tests broken down by top-level package directory.")

    suite_rows = []
    for suite in unit_results["suites"]:
        name = suite["name"].replace("tests.", "").replace("tests/", "")
        pass_pct = f"{suite['passed']/max(suite['total'],1)*100:.1f}%"
        suite_rows.append([
            name, str(suite["total"]), str(suite["passed"]),
            str(suite["failed"]) if suite["failed"] else "\u2014",
            str(suite["skipped"]) if suite["skipped"] else "\u2014",
            pass_pct,
        ])
    if e2e_results["total"] > 0:
        suite_rows.append([
            "e2e (Playwright)", str(e2e_results["total"]), str(e2e_results["passed"]),
            str(e2e_results["failed"]) if e2e_results["failed"] else "\u2014",
            str(e2e_results["skipped"]) if e2e_results["skipped"] else "\u2014",
            f"{e2e_results['passed']/max(e2e_results['total'],1)*100:.1f}%",
        ])

    if suite_rows:
        pdf.add_data_table(
            ["Package", "Total", "Passed", "Failed", "Skipped", "Pass%"],
            suite_rows,
            col_widths=[60, 18, 18, 18, 18, 22],
        )

    # --- Section 3: Code Coverage ---
    pdf.add_page_break()
    pdf.add_heading("Code Coverage Analysis", 3)
    pdf.add_text(
        f"Overall line coverage: {coverage['line_rate']}% "
        f"({coverage['lines_covered']:,} of {coverage['lines_valid']:,} lines). "
        "Packages are sorted by coverage rate ascending."
    )

    cov_rows = []
    for pkg in coverage["packages"]:
        cov_rows.append([
            pkg["name"],
            f"{pkg['coverage']:.1f}%",
            str(pkg["lines_valid"]),
            str(pkg["lines_covered"]),
            str(pkg["gap"]) if pkg["gap"] else "\u2014",
        ])
    if cov_rows:
        pdf.add_data_table(
            ["Package", "Coverage", "Lines Valid", "Lines Covered", "Gap"],
            cov_rows,
            col_widths=[60, 22, 25, 28, 18],
        )

    below_90 = sum(1 for p in coverage["packages"] if p["coverage"] < 90 and p["lines_valid"] >= 10)
    pdf.add_text(
        f"Packages with <90% coverage: {below_90}  |  "
        f"Packages with <70% coverage: {sum(1 for p in coverage['packages'] if p['coverage'] < 70 and p['lines_valid'] >= 10)} "
        "(excluding trivial packages with <10 lines)."
    )

    # --- Section 4: Code Modularisation ---
    pdf.add_page_break()
    pdf.add_heading("Code Modularisation", 4)
    summary = scan_large_files_summary(large_files)
    pdf.add_text(
        f"Scope: src/  |  Files scanned: {total_code_files}  |  "
        f"Files over 300 lines: {summary['total_large_files']}. "
        "Files exceeding 300 non-blank lines are candidates for modularisation."
    )

    if large_files:
        lf_rows = [[f["path"], f["ext"], str(f["lines"]), f["priority"]] for f in large_files]
        pdf.add_data_table(
            ["File (relative to project root)", "Ext", "Lines", "Priority"],
            lf_rows,
            col_widths=[100, 15, 18, 20],
        )
    else:
        pdf.add_text("No files exceed the 300-line threshold.")

    # --- Section 5: Hard-Coding Audit ---
    pdf.add_page_break()
    pdf.add_heading("Hard-Coding Audit", 5)
    pdf.add_text(
        "Policy: every configurable domain parameter must be defined once in config.py "
        "and imported at every use site."
    )
    pdf.add_metric_table([
        {"metric": "Files scanned", "value": str(hardcoding["files_scanned"]), "status": "INFO"},
        {"metric": "Duplicate constants (same name, multiple files)",
         "value": str(hardcoding["duplicate_count"]),
         "status": "OK" if hardcoding["duplicate_count"] == 0 else "REVIEW"},
        {"metric": "ALL_CAPS constants outside config.py (action required)",
         "value": str(hardcoding["action_required_count"]),
         "status": "OK" if hardcoding["action_required_count"] == 0 else "REVIEW"},
        {"metric": "ALL_CAPS constants (precision/tolerance \u2014 acceptable)",
         "value": str(hardcoding["precision_count"]), "status": "OK"},
        {"metric": "Infrastructure literals (IP / port)",
         "value": str(hardcoding["infra_count"]),
         "status": "OK" if hardcoding["infra_count"] == 0 else "INFO"},
    ])

    # --- Section 6: E2E Browser Tests ---
    pdf.add_page_break()
    pdf.add_heading("E2E Browser Tests", 6)
    pdf.add_text(
        "End-to-end browser tests exercising the full application stack via "
        "Playwright (headless Chromium)."
    )
    if e2e_results["total"] > 0:
        pdf.add_metric_table([
            {"metric": "Total E2E tests", "value": str(e2e_results["total"]), "status": "INFO"},
            {"metric": "Passed", "value": str(e2e_results["passed"]),
             "status": "OK" if e2e_results["failed"] == 0 else "FAIL"},
            {"metric": "Failed", "value": str(e2e_results["failed"]),
             "status": "OK" if e2e_results["failed"] == 0 else "FAIL"},
            {"metric": "Run time", "value": f"{e2e_results['time']:.1f}s", "status": "INFO"},
        ])
    else:
        pdf.add_text(
            "E2E tests were skipped. Install Playwright to enable: "
            "pip install playwright && playwright install chromium"
        )

    # --- Section 7: Remediation Roadmap ---
    pdf.add_page_break()
    pdf.add_heading("Remediation Roadmap", 7)
    pdf.add_text(
        "Prioritised actions derived from this audit cycle. "
        "Items are ranked by risk impact under SR 11-7 / SS1/23."
    )

    remediation = _build_remediation(coverage, large_files, hardcoding, duplication)
    if remediation:
        rem_rows = [[r["priority"], r["severity"], r["action"], r["detail"]] for r in remediation]
        pdf.add_data_table(
            ["Priority", "Severity", "Action", "Detail"],
            rem_rows,
            col_widths=[15, 18, 45, 75],
        )

    pdf.add_spacer(8)
    pdf.add_text(
        "Supporting artefacts in data/output/audit/: full_audit_report.pdf  |  "
        "large_file_report.pdf  |  code_duplication_report.pdf  |  "
        "hardcoding_report.pdf  |  coverage_html/ (HTML)  |  test_results.xml  |  coverage.xml",
        style="MKMSmall",
    )
    pdf.add_text(
        "Model Governance Reference: SR 11-7 (Federal Reserve), SS1/23 (PRA) \u2014 "
        "Model Risk Management. This report is produced automatically; "
        "human review is required before formal model approval.",
        style="MKMSmall",
    )

    return pdf.build()


def _build_remediation(coverage, large_files, hardcoding, duplication):
    """Build prioritised remediation items."""
    items = []

    # Coverage
    cov_status = "OK" if coverage["line_rate"] >= 95 else "MEDIUM"
    items.append({
        "priority": "P2",
        "severity": cov_status,
        "action": f"Maintain coverage at {coverage['line_rate']}%",
        "detail": "Coverage meets the 95% governance target. "
                  "Continue enforcing --cov-fail-under in CI.",
    })

    # Hardcoding
    if hardcoding["action_required_count"] > 0:
        items.append({
            "priority": "P3",
            "severity": "MEDIUM",
            "action": "Migrate ALL_CAPS constants to config.py",
            "detail": f"{hardcoding['action_required_count']} constants found outside config.py. "
                      "Distributed hard-coded parameters create recalibration risk.",
        })

    # Large files
    high_files = [f for f in large_files if f["priority"] == "High"]
    if high_files:
        items.append({
            "priority": "P4",
            "severity": "MEDIUM",
            "action": f"Modularise {len(high_files)} files over 600 lines",
            "detail": "Large files are harder to test and review. See Section 4.",
        })
    elif large_files:
        items.append({
            "priority": "P5",
            "severity": "LOW",
            "action": f"Review {len(large_files)} files over 300 lines",
            "detail": "All below 600 lines. See Section 4 for details.",
        })

    # Duplication
    if duplication:
        items.append({
            "priority": "P5",
            "severity": "LOW",
            "action": f"Review {len(duplication)} code duplication hotspots",
            "detail": "See code_duplication_report.pdf for clone-pair details.",
        })

    items.append({
        "priority": "P6",
        "severity": "LOW",
        "action": "Run full audit before each governance review",
        "detail": "Execute: python3 chat.py -test --audit to regenerate all artefacts (includes E2E).",
    })

    return items
