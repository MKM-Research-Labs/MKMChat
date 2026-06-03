# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Standalone audit reports — large files, hard-coding, and duplication."""

import os
from datetime import datetime

from .pdf_builder import MKMReportBuilder
from .scanners import (
    scan_large_files,
    scan_large_files_summary,
    count_all_code_files,
    scan_hardcoding,
    scan_duplication,
)


def generate_large_file_report(output_dir: str, project_root: str) -> str:
    """Generate the large file / modularisation report."""
    output_path = os.path.join(output_dir, "large_file_report.pdf")
    src_dir = os.path.join(project_root, "src")

    large_files = scan_large_files(src_dir)
    summary = scan_large_files_summary(large_files)
    total_files, total_lines = count_all_code_files(src_dir)

    pdf = MKMReportBuilder(output_path, "Code Modularisation Analysis")
    pdf.add_heading("Code Modularisation Analysis", 0)
    pdf.add_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.add_text(f"Project Root: {os.path.join(project_root, 'src')}")
    pdf.add_text("Threshold: Files with more than 300 lines")
    pdf.add_spacer(5)

    pdf.add_heading("Executive Summary", 0)
    pdf.add_metric_table([
        {"metric": "Total Code Files", "value": str(total_files), "status": "INFO"},
        {"metric": "Total Lines of Code", "value": f"{total_lines:,}", "status": "INFO"},
        {"metric": "Files Exceeding 300 Lines", "value": str(summary["total_large_files"]),
         "status": "OK" if summary["total_large_files"] == 0 else "REVIEW"},
        {"metric": "Lines in Large Files",
         "value": f"{summary['total_lines_in_large']:,} ({summary['total_lines_in_large']/max(total_lines,1)*100:.1f}% of total)",
         "status": "INFO"},
    ])

    if large_files:
        pdf.add_heading("Files Requiring Modularisation (>300 lines)", 0)
        rows = []
        for i, f in enumerate(large_files, 1):
            rows.append([str(i), f["path"], f["ext"], str(f["lines"]), f["priority"]])
        pdf.add_data_table(
            ["Rank", "File Path", "Type", "Lines", "Priority"],
            rows,
            col_widths=[10, 95, 12, 15, 20],
        )
    else:
        pdf.add_text("No files exceed the 300-line threshold. Well modularised.")

    return pdf.build()


def generate_hardcoding_report(output_dir: str, project_root: str) -> str:
    """Generate the hard-coding audit report."""
    output_path = os.path.join(output_dir, "hardcoding_report.pdf")
    src_dir = os.path.join(project_root, "src")

    results = scan_hardcoding(src_dir, os.path.join(project_root, "config.py"))

    pdf = MKMReportBuilder(output_path, "Hard-Coding Audit")
    pdf.add_heading("Hard-Coding Audit", 0)
    pdf.add_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.add_text(
        "Policy: every configurable domain parameter must be defined once in config.py "
        "and imported at every use site."
    )
    pdf.add_spacer(5)

    pdf.add_metric_table([
        {"metric": "Files scanned", "value": str(results["files_scanned"]), "status": "INFO"},
        {"metric": "Duplicate constants", "value": str(results["duplicate_count"]),
         "status": "OK" if results["duplicate_count"] == 0 else "REVIEW"},
        {"metric": "ALL_CAPS outside config.py (action required)",
         "value": str(results["action_required_count"]),
         "status": "OK" if results["action_required_count"] == 0 else "REVIEW"},
        {"metric": "Precision/tolerance constants (acceptable)",
         "value": str(results["precision_count"]), "status": "OK"},
        {"metric": "Infrastructure literals (IP/port)",
         "value": str(results["infra_count"]),
         "status": "OK" if results["infra_count"] == 0 else "INFO"},
    ])

    if results["action_required"]:
        pdf.add_heading("Constants Requiring Migration to config.py", 0)
        rows = [[f["file"], f["name"], f["value"]] for f in results["action_required"][:50]]
        pdf.add_data_table(["File", "Constant", "Value"], rows, col_widths=[70, 40, 50])

    if results["duplicates"]:
        pdf.add_heading("Duplicate Constants (same name in multiple files)", 0)
        for name, locs in list(results["duplicates"].items())[:20]:
            files = ", ".join(l["file"] for l in locs)
            pdf.add_text(f"<b>{name}</b>: {files}", "MKMBody")

    return pdf.build()


def generate_duplication_report(output_dir: str, project_root: str) -> str:
    """Generate the code duplication report."""
    output_path = os.path.join(output_dir, "code_duplication_report.pdf")
    src_dir = os.path.join(project_root, "src")

    clones = scan_duplication(src_dir)

    pdf = MKMReportBuilder(output_path, "Code Duplication Report")
    pdf.add_heading("Code Duplication Report", 0)
    pdf.add_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.add_text("Method: Token-based sliding window (6-line minimum block size)")
    pdf.add_spacer(5)

    pdf.add_metric_table([
        {"metric": "Clone pairs detected", "value": str(len(clones)),
         "status": "OK" if len(clones) == 0 else "REVIEW"},
    ])

    if clones:
        pdf.add_heading("Clone Pairs", 0)
        rows = []
        for c in clones[:30]:
            rows.append([
                c["file_a"], str(c["line_a"]),
                c["file_b"], str(c["line_b"]),
                str(c["lines"]),
            ])
        pdf.add_data_table(
            ["File A", "Line", "File B", "Line", "Lines"],
            rows,
            col_widths=[55, 12, 55, 12, 12],
        )
    else:
        pdf.add_text("No significant code duplication detected across source files.")

    return pdf.build()
