# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# rebuild_faiss_batch.py
"""
Overnight FAISS rebuild for a single knowledge base.

Wipes the existing FAISS index (and its processed-files tracker) for the chosen
knowledge base, then re-ingests every document from scratch in batches of N
(default 20). The FAISS index is saved to disk after each batch, so progress is
durable and the run can be stopped/restarted between batches.

This handles FAISS recreation ONLY. Summaries are a separate step.

Usage:
    python rebuild_faiss_batch.py                 # interactive: pick a KB, confirm
    python rebuild_faiss_batch.py --kb mods       # target MODS, still asks to confirm
    python rebuild_faiss_batch.py --kb mods --batch-size 20
    python rebuild_faiss_batch.py --list          # list knowledge bases and exit
    python rebuild_faiss_batch.py --kb mods --yes  # skip the typed confirmation (cron)
    python rebuild_faiss_batch.py --kb mods --resume  # continue without re-wiping

Run from the project root.
"""

import argparse
import os
import sys
import time
from datetime import datetime


def _apply_thread_limit():
    """Cap CPU threads BEFORE numpy/torch are imported (env vars are only read
    at import time). Driven by --threads N or the REFAISS_THREADS env var.
    Pass --threads 1 to keep the machine responsive / run on effectively one core.
    """
    n = os.environ.get("REFAISS_THREADS")
    argv = sys.argv
    for i, a in enumerate(argv):
        if a == "--threads" and i + 1 < len(argv):
            n = argv[i + 1]
        elif a.startswith("--threads="):
            n = a.split("=", 1)[1]
    if not n:
        return None
    try:
        n = max(1, int(n))
    except ValueError:
        return None
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[var] = str(n)
    return n


_THREAD_LIMIT = _apply_thread_limit()

# Ensure the project root is importable when run as a script.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import get_all_collections, get_collection_config, paths
from src.loaders import SUPPORTED_EXTENSIONS
from src.utils.file_utils import get_supported_files
from src.proc.processor import DocumentProcessor

FAISS_INDEX_FILES = ("index.faiss", "index.pkl")


# ---------------------------------------------------------------------------
# Logging: write to console and a timestamped log file for overnight review.
# ---------------------------------------------------------------------------
class _Tee:
    """Duplicate writes to multiple streams (console + log file)."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for stream in self._streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self._streams:
            stream.flush()

    def isatty(self):
        # Report the terminal-ness of the primary (console) stream so tqdm and
        # other TTY-aware code behave correctly.
        first = self._streams[0]
        return first.isatty() if hasattr(first, "isatty") else False

    def __getattr__(self, name):
        # Delegate anything else (encoding, fileno, etc.) to the primary stream.
        return getattr(self._streams[0], name)


def log(message=""):
    """Print a timestamped line."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {message}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def list_collections():
    """Print available knowledge bases with doc counts."""
    print("\nAvailable knowledge bases:")
    print(f"  {'CODE':<6} {'NAME':<16} {'DOCS':>6}  DESCRIPTION")
    print("  " + "-" * 70)
    for code, cfg in get_all_collections().items():
        docs_folder = cfg["docs_folder"]
        try:
            count = len(get_supported_files(docs_folder, SUPPORTED_EXTENSIONS))
        except Exception:
            count = "?"
        print(f"  {code:<6} {cfg['name']:<16} {str(count):>6}  {cfg['description']}")
    print()


def count_remaining(processor):
    """Number of files still needing processing (uses the processor's own logic)."""
    processed = processor.load_processed_files()
    all_files = get_supported_files(processor.docs_folder, SUPPORTED_EXTENSIONS)
    needing = processor._get_files_needing_processing(all_files, processed, False)
    return len(needing), len(all_files)


def wipe_faiss(collection_code):
    """Delete the FAISS index files and processed-files tracker for a KB."""
    cfg = get_collection_config(collection_code)
    faiss_dir = cfg["faiss_index"]
    processed_file = cfg["processed_file"]

    removed = []

    for name in FAISS_INDEX_FILES:
        target = os.path.join(faiss_dir, name)
        if os.path.exists(target):
            size_mb = os.path.getsize(target) / (1024 * 1024)
            os.remove(target)
            removed.append(f"{name} ({size_mb:.1f} MB)")

    if os.path.exists(processed_file):
        os.remove(processed_file)
        removed.append(os.path.basename(processed_file))

    if removed:
        for item in removed:
            log(f"  removed {item}")
    else:
        log("  nothing to remove (already clean)")


def confirm_wipe(collection_code, cfg, doc_count, skip):
    """Require the user to type the KB code before a destructive wipe."""
    faiss_dir = cfg["faiss_index"]
    print()
    print("=" * 72)
    print("  DESTRUCTIVE OPERATION — FAISS REBUILD")
    print("=" * 72)
    print(f"  Knowledge base : {collection_code}  ({cfg['name']})")
    print(f"  Documents      : {doc_count} files in {cfg['docs_folder']}")
    print(f"  FAISS index    : {faiss_dir}")
    print(f"  Tracker        : {cfg['processed_file']}")
    print()
    print("  The existing FAISS index and processed-files tracker for this KB")
    print("  will be DELETED, then rebuilt from scratch. Summaries are untouched.")
    print("=" * 72)

    if skip:
        log("Confirmation skipped (--yes).")
        return True

    try:
        answer = input(f"\nType the KB code '{collection_code}' to proceed (anything else aborts): ").strip()
    except EOFError:
        answer = ""

    if answer != collection_code:
        print("Aborted — no changes made.")
        return False
    return True


# ---------------------------------------------------------------------------
# Main rebuild loop
# ---------------------------------------------------------------------------
def rebuild(collection_code, batch_size, resume):
    cfg = get_collection_config(collection_code)

    if _THREAD_LIMIT:
        try:
            import torch
            torch.set_num_threads(_THREAD_LIMIT)
        except Exception:
            pass
        log(f"CPU threads capped at {_THREAD_LIMIT}.")

    processor = DocumentProcessor(docs_type=collection_code)
    processor.max_documents = batch_size      # one batch per process_documents() call
    processor.show_progress = True
    processor._init_handlers()                # re-init handlers with updated settings

    if not resume:
        log(f"Wiping FAISS for '{collection_code}'...")
        wipe_faiss(collection_code)
    else:
        log("Resume mode: keeping existing FAISS and tracker, continuing where it left off.")

    remaining, total = count_remaining(processor)
    if total == 0:
        log(f"No supported documents found in {processor.docs_folder}. Nothing to do.")
        return False

    log(f"Starting rebuild: {remaining} of {total} documents need processing "
        f"(batch size {batch_size}).")

    batch_num = 0
    run_start = time.time()
    prev_remaining = None

    while remaining > 0:
        batch_num += 1
        done = total - remaining
        log("-" * 60)
        log(f"BATCH {batch_num}: {done}/{total} done, {remaining} remaining.")
        batch_start = time.time()

        try:
            ok = processor.process_documents(force_reprocess=False)
        except Exception as exc:  # keep the overnight run alive across a bad batch
            log(f"  ERROR during batch {batch_num}: {exc}")
            import traceback
            traceback.print_exc()
            ok = None

        elapsed = time.time() - batch_start
        log(f"BATCH {batch_num} finished in {elapsed:.0f}s (result={ok}).")

        remaining, total = count_remaining(processor)

        # Stall guard: if a batch makes no progress, stop rather than loop forever
        # (e.g. a document that keeps failing to yield chunks).
        if prev_remaining is not None and remaining >= prev_remaining:
            log("No progress made this batch — stopping to avoid an infinite loop.")
            log("Inspect the log above for the offending document(s).")
            break
        prev_remaining = remaining

    total_elapsed = time.time() - run_start
    done = total - remaining
    log("=" * 60)
    log(f"DONE. {done}/{total} documents ingested across {batch_num} batches "
        f"in {total_elapsed / 60:.1f} min.")
    if remaining > 0:
        log(f"WARNING: {remaining} document(s) still unprocessed — see errors above.")
    else:
        log("FAISS index fully rebuilt. Summaries can be run next.")
    return remaining == 0


def main():
    parser = argparse.ArgumentParser(
        description="Wipe and rebuild a knowledge base's FAISS index in batches."
    )
    parser.add_argument("--kb", "--collection", dest="kb",
                        help="Knowledge base code (e.g. mods). Omit to choose interactively.")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="Documents per batch; FAISS is saved after each (default 20).")
    parser.add_argument("--threads", type=int, metavar="N",
                        help="Cap CPU threads (e.g. 1 to run on ~one core and keep the "
                             "machine responsive). Applied before model load.")
    parser.add_argument("--list", action="store_true",
                        help="List knowledge bases and exit.")
    parser.add_argument("--yes", action="store_true",
                        help="Skip the typed confirmation (for cron/unattended use).")
    parser.add_argument("--resume", action="store_true",
                        help="Do NOT wipe; continue an interrupted rebuild from its tracker.")
    args = parser.parse_args()

    # Tee output to a timestamped log file alongside the json data dir.
    log_dir = paths.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"rebuild_faiss_{args.kb or 'kb'}_{stamp}.log"
    log_file = open(log_path, "a", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, log_file)
    sys.stderr = _Tee(sys.__stderr__, log_file)

    collections = get_all_collections()

    if args.list:
        list_collections()
        return 0

    if args.batch_size < 1:
        print("--batch-size must be >= 1.")
        return 2

    # Resolve the target KB.
    kb = args.kb
    if not kb:
        list_collections()
        try:
            kb = input("Enter the KB code to completely clean out and rebuild: ").strip()
        except EOFError:
            kb = ""

    if kb not in collections:
        print(f"Unknown knowledge base: '{kb}'. Valid codes: {', '.join(collections)}")
        return 2

    cfg = get_collection_config(kb)
    log(f"Logging to {log_path}")

    doc_count = len(get_supported_files(cfg["docs_folder"], SUPPORTED_EXTENSIONS))

    if not args.resume:
        if not confirm_wipe(kb, cfg, doc_count, args.yes):
            return 1

    success = rebuild(kb, args.batch_size, args.resume)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
