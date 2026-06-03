#!/usr/bin/env python3
# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Unified entry point for the MKM Research Document Processor and Q&A Application.

Handles document processing, summarization, and web interface.
"""

import sys
import os
import argparse
import json
import hashlib
import importlib
import logging

# Suppress the "UNEXPECTED embeddings.position_ids" warning from transformers
# This is a known harmless warning: newer all-MiniLM-L6-v2 weights compute
# position_ids at runtime rather than storing them.
logging.getLogger("transformers.utils.loading_report").setLevel(logging.ERROR)

from src.app import DocumentQAApp
from src.document_processor import DocumentProcessor
from config import get_collection_config, get_all_collections, CONFIG


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="MKM Research Document Processor and Q&A Application"
    )

    # Mode selection
    parser.add_argument(
        "-web-only",
        action="store_true",
        help="Skip all processing and go directly to web interface",
    )
    parser.add_argument(
        "-process-only",
        action="store_true",
        help="Only process documents without starting web interface",
    )
    parser.add_argument(
        "-summarize-only",
        action="store_true",
        help="Only run summarization without document processing or web interface",
    )
    parser.add_argument(
        "-list-summaries",
        action="store_true",
        help="List all summarized documents without processing",
    )
    parser.add_argument(
        "-test",
        action="store_true",
        help="Run test suite with coverage and generate audit reports",
    )
    parser.add_argument(
        "-test-e2e",
        action="store_true",
        help="Run Playwright E2E browser tests",
    )
    parser.add_argument(
        "-test-all",
        action="store_true",
        help="Run all test suites (unit + E2E + JS)",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Generate PDF audit reports (use with -test or standalone)",
    )

    # Web server options
    parser.add_argument(
        "--port",
        type=int,
        default=CONFIG["server_port"],
        help=f"Port to run the web server on (default: {CONFIG['server_port']})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=CONFIG["server_host"],
        help=f"Host to bind the web server to (default: {CONFIG['server_host']})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=True,
        help="Run Flask in debug mode (default: True)",
    )

    # Collection selection - dynamically built from config
    collection_keys = list(get_all_collections().keys())
    parser.add_argument(
        "--collection",
        choices=collection_keys + ["all"],
        default="all",
        help=f"Document collection to process: {', '.join(collection_keys)}, or all (default: all)",
    )

    # Document processing options
    parser.add_argument(
        "--max-docs",
        type=int,
        default=50,
        help="Maximum number of documents to process (default: 50)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of all documents",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars",
    )
    parser.add_argument(
        "--alt-embeddings",
        action="store_true",
        help="Use alternative embedding models",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Run diagnostics on problematic files",
    )

    # Summarization options
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Run document summarization after processing",
    )
    parser.add_argument(
        "--clean-summaries",
        action="store_true",
        help="Clear existing summaries before processing",
    )

    return parser.parse_args()


def load_json_file(file_path, default=None):
    """Load JSON file with error handling."""
    if default is None:
        default = {}
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return default


def get_file_hash(file_path):
    """Get SHA-256 hash of file content."""
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()
    except IOError as e:
        print(f"Warning: Could not hash {file_path}: {e}")
        return ""


def process_collection(collection_type, args):
    """Process a specific document collection."""
    print(f"\n{'=' * 50}")
    print(f"Processing {collection_type.upper()} document collection")
    print(f"{'=' * 50}")

    processor = DocumentProcessor(docs_type=collection_type)
    processor.max_documents = args.max_docs
    processor.show_progress = not args.no_progress

    if args.alt_embeddings:
        processor.setup_alternative_embeddings()

    if args.diagnose:
        processor.diagnose_and_report_problematic_files()
        # diagnostics-only is allowed to exit early
        if args.process_only and not args.force and not args.summarize:
            return True

    # Process documents
    try:
        processor.process_documents(force_reprocess=args.force)
        print(
            f"✅ {collection_type.upper()} collection processing completed successfully"
        )
        return True
    except Exception as e:
        print(f"❌ Error processing {collection_type} collection: {str(e)}")
        return False


def summarize_collection(collection_type, args):
    """Run summarization for a specific collection."""
    print(f"\n{'=' * 50}")
    print(f"Summarizing {collection_type.upper()} document collection")
    print(f"{'=' * 50}")

    try:
        processor = DocumentProcessor(docs_type=collection_type)
        success = processor.summarize_documents(
            max_docs=args.max_docs,
            force_reprocess=args.force,
            clean=args.clean_summaries,
        )

        if success:
            print(
                f"✅ {collection_type.upper()} collection summarization completed successfully"
            )
            return True
        else:
            print(f"❌ {collection_type.upper()} collection summarization failed")
            return False

    except Exception as e:
        print(f"❌ Error summarizing {collection_type} collection: {str(e)}")
        return False


def list_collection_summaries(collection_type):
    """List summary status for a specific collection."""
    processor = DocumentProcessor(docs_type=collection_type)
    collection_config = get_collection_config(collection_type)
    summary_file = collection_config["summary_file"]
    docs_folder = collection_config["docs_folder"]

    print(f"\nCollection: {collection_type.upper()}")
    print(f"Documents folder: {docs_folder}")
    print(f"Summary file:     {summary_file}")

    if not os.path.isdir(docs_folder):
        print("No documents folder found, nothing to list.")
        return

    # Get all documents in the folder
    all_docs = [
        f
        for f in os.listdir(docs_folder)
        if os.path.isfile(os.path.join(docs_folder, f))
    ]

    # Load summarized files data
    summarised_files = load_json_file(summary_file, default={})

    # Check status for each file
    summarized_count = 0
    unsummarized_count = 0
    changed_count = 0

    for doc in sorted(all_docs):
        doc_path = os.path.join(docs_folder, doc)
        current_hash = get_file_hash(doc_path)

        if doc in summarised_files:
            if summarised_files[doc]["hash"] == current_hash:
                summary_type = summarised_files[doc].get("summary_type", "FULL")
                print(f"✓ SUMMARIZED ({summary_type}): {doc}")
                summarized_count += 1
            else:
                print(f"⚠ CHANGED : {doc} (needs updating)")
                changed_count += 1
        else:
            print(f"✗ PENDING : {doc}")
            unsummarized_count += 1

    print("\nSUMMARY:")
    print(f"Total Documents: {len(all_docs)}")
    print(f" - Summarized: {summarized_count}")
    print(f" - Changed (needs update): {changed_count}")
    print(f" - Pending: {unsummarized_count}")
    print(f"\nSummarization Record: {summary_file}")

    # Print summary sample for the first fully up‑to‑date summarized document
    if summarized_count > 0:
        for doc in sorted(all_docs):
            if doc in summarised_files:
                stored_hash = summarised_files[doc]["hash"]
                current_hash = get_file_hash(os.path.join(docs_folder, doc))
                if stored_hash == current_hash:
                    summary = summarised_files[doc].get("summary", "")
                    if summary:
                        print("\nSample Summary (first 200 characters):")
                        print("-" * 60)
                        print(f"{summary[:200]}...")
                    break


def run_cleanup():
    """Run cleanup for all document collections that have cleaners."""
    collections = get_all_collections()
    
    for collection_type, config in collections.items():
        cleanup_module_path = config.get("cleanup_module")
        if cleanup_module_path:
            try:
                print(f"🧹 Cleaning up {collection_type.upper()} documents...")
                module = importlib.import_module(cleanup_module_path)
                if hasattr(module, "main"):
                    module.main()
                else:
                    print(f"  Warning: No main() function in {cleanup_module_path}")
            except ImportError as e:
                print(f"  Warning: Could not import cleanup module for {collection_type}: {e}")


def _resolve_collections_arg(arg_collection: str):
    """Map CLI --collection to actual collection list using CONFIG."""
    all_keys = list(get_all_collections().keys())
    if arg_collection == "all":
        return all_keys
    else:
        return [arg_collection]


def run_processing(args):
    """Run document processing for selected collections."""
    collections = _resolve_collections_arg(args.collection)
    results = {}
    for collection in collections:
        results[collection] = process_collection(collection, args)
    return all(results.values()), results


def run_summarization(args):
    """Run summarization for selected collections."""
    collections = _resolve_collections_arg(args.collection)
    results = {}
    for collection in collections:
        results[collection] = summarize_collection(collection, args)
    return all(results.values()), results


def list_summaries(args):
    """List summaries for selected collections."""
    collections = _resolve_collections_arg(args.collection)
    for collection in collections:
        print(f"\n{'=' * 50}")
        print(f"SUMMARIES FOR {collection.upper()} DOCUMENTS")
        print(f"{'=' * 50}")
        list_collection_summaries(collection)


def run_tests(mode="unit"):
    """Run test suites and generate audit reports.

    Args:
        mode: 'unit' for pytest unit tests, 'e2e' for Playwright, 'all' for everything
    """
    import subprocess

    project_root = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(project_root, "data", "output", "audit"), exist_ok=True)

    if mode == "unit":
        print("=" * 60)
        print("RUNNING UNIT TESTS WITH COVERAGE")
        print("=" * 60)
        cmd = [
            sys.executable, "-m", "pytest", "tests/",
            "--ignore=tests/e2e", "--ignore=tests/js",
            "-m", "not integration",
            "-q",
            "--cov=src",
            "--cov-report=html:data/output/audit/coverage_html",
            "--cov-report=xml:data/output/audit/coverage.xml",
            "--cov-report=term-missing",
            "--junitxml=data/output/audit/test_results.xml",
        ]
    elif mode == "e2e":
        print("=" * 60)
        print("RUNNING E2E TESTS (PLAYWRIGHT)")
        print("=" * 60)
        cmd = [
            sys.executable, "-m", "pytest", "tests/e2e/",
            "-v",
            "--junitxml=data/output/audit/e2e_results.xml",
        ]
    elif mode == "all":
        # Run unit first, then E2E
        print("=" * 60)
        print("RUNNING ALL TEST SUITES")
        print("=" * 60)
        unit_result = run_tests("unit")
        e2e_result = run_tests("e2e")
        return max(unit_result, e2e_result)
    else:
        print(f"Unknown test mode: {mode}")
        return 1

    result = subprocess.run(cmd, cwd=project_root)

    if mode == "unit" and result.returncode == 0:
        print("\nAudit reports generated:")
        print(f"  Coverage HTML: data/output/audit/coverage_html/index.html")
        print(f"  Coverage XML:  data/output/audit/coverage.xml")
        print(f"  JUnit XML:     data/output/audit/test_results.xml")

    return result.returncode


def run_audit_reports():
    """Generate PDF audit reports from the latest test results."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(project_root, "data", "output", "audit")

    from src.audit import generate_all_reports
    reports = generate_all_reports(output_dir, project_root)
    return 0 if reports else 1


def start_web_application(args):
    """Start the Flask web application."""
    print("\n" + "=" * 60)
    print("STARTING WEB APPLICATION")
    print("=" * 60)
    print(f"🚀 Starting web server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")

    try:
        app = DocumentQAApp()
        app.run(debug=args.debug, port=args.port, host=args.host)
    except KeyboardInterrupt:
        print("\n⛔️ Shutting down gracefully...")
        return 0
    except Exception as e:
        print(f"❌ Error starting web application: {str(e)}")
        return 1
    return 0


def main():
    """Main entry point"""

    # Check if this is the Flask reloader process
    is_reloader_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    args = parse_arguments()

    # Only run document operations in the main process (not the reloader)
    if not is_reloader_process:
        # Handle test modes
        # When --audit is combined with -test, escalate to full suite
        # so the audit report includes E2E results.
        if args.test:
            mode = "all" if args.audit else "unit"
            result = run_tests(mode)
            if args.audit:
                run_audit_reports()
            return result
        if args.test_e2e:
            result = run_tests("e2e")
            if args.audit:
                run_audit_reports()
            return result
        if args.test_all:
            result = run_tests("all")
            if args.audit:
                run_audit_reports()
            return result
        if args.audit:
            # Standalone audit (no test re-run)
            return run_audit_reports()

        # Handle list-summaries mode
        if args.list_summaries:
            list_summaries(args)
            return 0

        # Handle summarize-only mode
        if args.summarize_only:
            print("=" * 60)
            print("RUNNING SUMMARIZATION ONLY")
            print("=" * 60)
            all_success, results = run_summarization(args)
            if all_success:
                print("\n✅ All summarization completed successfully!")
                return 0
            else:
                print("\n❌ Some summarization failed!")
                for collection, success in results.items():
                    if not success:
                        print(f" - {collection.upper()} collection summarization failed")
                return 1

        # Handle web-only mode
        if args.web_only:
            print("⏭️ Skipping document processing as requested...")

        # Handle process-only or standard mode
        elif args.process_only or not args.web_only:
            print("=" * 60)
            print("STARTING DOCUMENT PROCESSING")
            print("=" * 60)

            # Run cleanup
            run_cleanup()

            # Process documents
            all_success, results = run_processing(args)

            if not all_success:
                print("\n❌ Some document processing failed!")
                for collection, success in results.items():
                    if not success:
                        print(f" - {collection.upper()} collection failed")
                if args.process_only or not args.summarize:
                    user_input = input("\nContinue anyway? (y/N): ")
                    if user_input.lower() != "y":
                        return 1
            else:
                print("\n✅ All document processing completed successfully!")

            # Run summarization if requested
            if args.summarize:
                print("\n" + "=" * 60)
                print("STARTING DOCUMENT SUMMARIZATION")
                print("=" * 60)

                all_success_sum, results_sum = run_summarization(args)
                if not all_success_sum:
                    print("\n❌ Some summarization failed!")
                    for collection, success in results_sum.items():
                        if not success:
                            print(
                                f" - {collection.upper()} collection summarization failed"
                            )
                    if not args.process_only:
                        user_input = input(
                            "\nContinue to web interface anyway? (y/N): "
                        )
                        if user_input.lower() != "y":
                            return 1
                else:
                    print("\n✅ All summarization completed successfully!")

            # Exit if process-only mode
            if args.process_only:
                print("\nProcessing complete!")
                return 0

    # Start web application (runs in both parent and reloader processes)
    return start_web_application(args)


if __name__ == "__main__":
    sys.exit(main())