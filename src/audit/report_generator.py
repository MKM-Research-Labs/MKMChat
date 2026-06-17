# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
