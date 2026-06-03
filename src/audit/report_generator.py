# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Audit report orchestrator — coordinates generation of all audit PDFs."""

import os
from typing import List

from .full_report import generate_full_audit_report
from .standalone_reports import (
    generate_large_file_report,
    generate_hardcoding_report,
    generate_duplication_report,
)


def generate_all_reports(output_dir: str, project_root: str) -> List:
    """Generate all audit PDF reports."""
    os.makedirs(output_dir, exist_ok=True)

    reports = []
    print("\nGenerating audit reports...")

    print("  [1/4] Full audit report...")
    reports.append(generate_full_audit_report(output_dir, project_root))

    print("  [2/4] Large file report...")
    reports.append(generate_large_file_report(output_dir, project_root))

    print("  [3/4] Hard-coding report...")
    reports.append(generate_hardcoding_report(output_dir, project_root))

    print("  [4/4] Code duplication report...")
    reports.append(generate_duplication_report(output_dir, project_root))

    print(f"\n  All {len(reports)} reports generated in {output_dir}/")
    for r in reports:
        print(f"    - {os.path.basename(r)}")

    return reports
