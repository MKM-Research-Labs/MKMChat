# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Static analysis scanners for audit reports."""

import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Any
from collections import defaultdict


def scan_large_files(
    src_dir: str, threshold: int = 300, extensions: tuple = (".py", ".js", ".css")
) -> List[Dict[str, Any]]:
    """Scan for files exceeding a line count threshold.

    Returns list of dicts: {path, ext, lines, priority}
    """
    results = []
    src_path = Path(src_dir)

    for ext in extensions:
        for fpath in src_path.rglob(f"*{ext}"):
            if "__pycache__" in str(fpath) or "node_modules" in str(fpath):
                continue
            try:
                lines = sum(1 for line in open(fpath, "r", errors="replace") if line.strip())
                if lines > threshold:
                    priority = "High" if lines > 600 else ("Medium" if lines > 450 else "Low")
                    results.append({
                        "path": str(fpath.relative_to(src_path.parent)),
                        "ext": ext,
                        "lines": lines,
                        "priority": priority,
                    })
            except Exception:
                continue

    results.sort(key=lambda x: x["lines"], reverse=True)
    return results


def scan_large_files_summary(results: List[Dict]) -> Dict[str, Any]:
    """Compute summary statistics for large file scan."""
    return {
        "total_large_files": len(results),
        "total_lines_in_large": sum(r["lines"] for r in results),
        "by_extension": _count_by_key(results, "ext"),
        "by_priority": _count_by_key(results, "priority"),
    }


def _count_by_key(items: List[Dict], key: str) -> Dict[str, int]:
    counts = defaultdict(int)
    for item in items:
        counts[item[key]] += 1
    return dict(counts)


def count_all_code_files(
    src_dir: str, extensions: tuple = (".py", ".js", ".css")
) -> Tuple[int, int]:
    """Count total code files and total lines."""
    total_files = 0
    total_lines = 0
    src_path = Path(src_dir)
    for ext in extensions:
        for fpath in src_path.rglob(f"*{ext}"):
            if "__pycache__" in str(fpath) or "node_modules" in str(fpath):
                continue
            try:
                total_files += 1
                total_lines += sum(1 for _ in open(fpath, "r", errors="replace"))
            except Exception:
                continue
    return total_files, total_lines


# ---------------------------------------------------------------------------
# Hard-coding scanner
# ---------------------------------------------------------------------------

# Pattern for ALL_CAPS assignments: MY_CONST = value
_ALLCAPS_PATTERN = re.compile(r"^([A-Z][A-Z0-9_]{2,})\s*=\s*(.+)$")

# Categories
_INFRA_PATTERNS = re.compile(r"(127\.0\.0\.1|localhost|:\d{4}|https?://)", re.I)
_PRECISION_NAMES = {"EPSILON", "TOLERANCE", "PRECISION", "DECIMAL_PLACES", "ROUND_DP"}


def scan_hardcoding(
    src_dir: str, config_path: str = "config.py"
) -> Dict[str, Any]:
    """Scan for hard-coded constants outside config.py.

    Returns dict with categories: duplicates, infra_literals, inline_params,
    precision_constants, action_required.
    """
    src_path = Path(src_dir)
    config_file = Path(config_path).name

    constants_by_name: Dict[str, List[Dict]] = defaultdict(list)
    all_findings = []
    files_scanned = 0

    for fpath in src_path.rglob("*.py"):
        if "__pycache__" in str(fpath) or fpath.name == config_file:
            continue
        files_scanned += 1
        try:
            for lineno, line in enumerate(open(fpath, "r", errors="replace"), 1):
                line = line.strip()
                if line.startswith("#") or line.startswith("\"\"\""):
                    continue
                m = _ALLCAPS_PATTERN.match(line)
                if m:
                    name, value = m.group(1), m.group(2).strip()
                    # Skip common non-domain patterns
                    if name.startswith("_") or name in {"__all__", "TYPE_CHECKING"}:
                        continue
                    rel_path = str(fpath.relative_to(src_path.parent))
                    entry = {"name": name, "value": value[:80], "file": rel_path, "line": lineno}
                    constants_by_name[name].append(entry)
                    all_findings.append(entry)
        except Exception:
            continue

    # Categorize
    duplicates = {n: locs for n, locs in constants_by_name.items() if len(locs) > 1}
    infra = [f for f in all_findings if _INFRA_PATTERNS.search(f["value"])]
    precision = [f for f in all_findings if f["name"] in _PRECISION_NAMES]
    action_required = [
        f for f in all_findings
        if f["name"] not in _PRECISION_NAMES
        and not _INFRA_PATTERNS.search(f["value"])
        and f["name"] not in duplicates
    ]

    return {
        "files_scanned": files_scanned,
        "total_findings": len(all_findings),
        "duplicates": duplicates,
        "duplicate_count": len(duplicates),
        "infra_literals": infra,
        "infra_count": len(infra),
        "precision_constants": precision,
        "precision_count": len(precision),
        "action_required": action_required,
        "action_required_count": len(action_required),
    }


# ---------------------------------------------------------------------------
# Code duplication scanner (simple token-based)
# ---------------------------------------------------------------------------

def scan_duplication(
    src_dir: str, min_lines: int = 6, similarity_threshold: float = 0.85
) -> List[Dict[str, Any]]:
    """Scan for near-duplicate code blocks across Python files.

    Uses a sliding window of `min_lines` lines, hashed for comparison.
    Returns list of clone pairs.
    """
    src_path = Path(src_dir)
    block_index: Dict[str, List[Dict]] = defaultdict(list)  # hash -> locations

    for fpath in src_path.rglob("*.py"):
        if "__pycache__" in str(fpath) or "test" in str(fpath).lower():
            continue
        try:
            lines = [
                l.strip() for l in open(fpath, "r", errors="replace").readlines()
                if l.strip() and not l.strip().startswith("#")
            ]
        except Exception:
            continue

        rel_path = str(fpath.relative_to(src_path.parent))

        # Sliding window
        for i in range(len(lines) - min_lines + 1):
            block = "\n".join(lines[i : i + min_lines])
            # Skip trivial blocks (imports, empty classes)
            if all(l.startswith(("import ", "from ", "\"\"\"", "'''", "pass", "return")) for l in lines[i:i+min_lines]):
                continue
            h = hashlib.md5(block.encode()).hexdigest()
            block_index[h].append({"file": rel_path, "start_line": i + 1, "block": block})

    # Find clones (same hash, different files)
    clones = []
    seen_pairs = set()
    for h, locations in block_index.items():
        if len(locations) < 2:
            continue
        # Group by unique files
        files = list({loc["file"] for loc in locations})
        if len(files) < 2:
            continue
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                pair_key = tuple(sorted([files[i], files[j]]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                loc_a = next(l for l in locations if l["file"] == files[i])
                loc_b = next(l for l in locations if l["file"] == files[j])
                clones.append({
                    "file_a": files[i],
                    "line_a": loc_a["start_line"],
                    "file_b": files[j],
                    "line_b": loc_b["start_line"],
                    "lines": min_lines,
                    "preview": loc_a["block"][:120],
                })

    return clones
