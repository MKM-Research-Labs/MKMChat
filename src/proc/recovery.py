# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""
Recovery and diagnostics for problematic documents.
Handles error recovery and diagnostic reporting.
"""

import os
from datetime import datetime
from langchain_core.documents import Document

from ..utils.text_utils import sanitize_text, standardize_metadata
from ..utils.file_utils import get_file_hash, save_json_file
from ..utils.diagnostics import diagnose_pdf


class RecoveryHandler:
    """Handles recovery of problematic documents."""

    def __init__(self, docs_folder, text_splitter, docs_type, processed_files_path):
        """
        Initialize the recovery handler.

        Args:
            docs_folder (str): Path to documents folder
            text_splitter: Text splitter instance
            docs_type (str): Document collection type
            processed_files_path (str): Path to processed files JSON
        """
        self.docs_folder = docs_folder
        self.text_splitter = text_splitter
        self.docs_type = docs_type
        self.processed_files_path = processed_files_path

    def handle_problematic_document(self, filename, processed_files, error_msg=None):
        """
        Handle problematic documents by attempting recovery.

        Args:
            filename (str): Name of the problematic file
            processed_files (dict): Dictionary of processed file records
            error_msg (str, optional): Error message from processing attempt

        Returns:
            list or None: List of recovered document chunks if successful
        """
        file_path = os.path.join(self.docs_folder, filename)
        file_hash = get_file_hash(file_path)

        # Record failure in processed files
        processed_files[filename] = {
            'hash': file_hash,
            'processed_date': datetime.now().isoformat(),
            'num_chunks': 0,
            'status': 'ERROR_HANDLED',
            'error': error_msg or "Unknown error during processing"
        }

        # Check for binary content issues
        if not self._is_binary_error(error_msg):
            return None

        print(f"Detected binary content issue in {filename}")
        return self._attempt_binary_recovery(filename, file_path, file_hash, processed_files)

    def _is_binary_error(self, error_msg):
        """Check if error indicates binary content issue."""
        if not error_msg:
            return False
        binary_indicators = [
            'Invalid Elementary Object',
            "can't concat str to ByteStringObject",
            "stream filter 'FlateDecode'"
        ]
        return any(indicator in error_msg for indicator in binary_indicators)

    def _attempt_binary_recovery(self, filename, file_path, file_hash, processed_files):
        """
        Attempt binary-safe extraction from PDF.

        Args:
            filename (str): Name of the file
            file_path (str): Full path to file
            file_hash (str): File hash
            processed_files (dict): Processed files dictionary

        Returns:
            list or None: Recovered chunks or None
        """
        try:
            from ..loaders.pdf_loader import EnhancedPDFLoader
            print(f"Applying special binary-safe handling for {filename}...")

            loader = EnhancedPDFLoader(file_path)
            pages = loader.load()

            if not pages:
                print(f"Recovery attempt failed for {filename}")
                return None

            # Sanitize page content
            sanitized_pages = []
            for page in pages:
                if isinstance(page.page_content, str) and page.page_content.startswith('[Error'):
                    continue
                sanitized_page = Document(
                    page_content=sanitize_text(page.page_content),
                    metadata=page.metadata
                )
                sanitized_pages.append(sanitized_page)

            if not sanitized_pages:
                print(f"Recovery attempt failed for {filename}")
                return None

            # Split into chunks
            chunks = self.text_splitter.split_documents(sanitized_pages)

            if not chunks:
                print(f"Recovery attempt failed for {filename}")
                return None

            chunks = standardize_metadata(chunks, self.docs_type)

            # Update processed files to successful
            processed_files[filename] = {
                'hash': file_hash,
                'processed_date': datetime.now().isoformat(),
                'num_chunks': len(chunks),
                'status': 'RECOVERED',
                'recovery_method': 'binary_safe_extraction'
            }
            print(f"Successfully recovered {len(chunks)} chunks from {filename}")
            return chunks

        except Exception as recovery_error:
            print(f"Error during recovery attempt: {str(recovery_error)}")
            processed_files[filename]['error'] += f" | Recovery failed: {str(recovery_error)}"
            return None

    def diagnose_and_report(self, processed_files):
        """
        Run diagnostics on all error files and generate a report.

        Args:
            processed_files (dict): Dictionary of processed file records

        Returns:
            list: List of diagnostic reports
        """
        error_files = {
            filename: info for filename, info in processed_files.items()
            if info.get('status') == 'ERROR'
        }

        if not error_files:
            print(f"No error files found in {self.processed_files_path}")
            return []

        print(f"\nRunning diagnostics on {len(error_files)} problematic files...")

        diagnostic_reports = []

        for filename in error_files:
            file_path = os.path.join(self.docs_folder, filename)

            if not os.path.exists(file_path):
                print(f"Cannot diagnose {filename} - file not found")
                continue

            print(f"Diagnosing {filename}...")
            try:
                diagnostic = diagnose_pdf(file_path)
                diagnostic_reports.append(diagnostic)

                print(f"  Assessment: {diagnostic['overall_assessment']}")
                if diagnostic['issues_detected']:
                    print(f"  Issues: {', '.join(diagnostic['issues_detected'])}")
                print(f"  Recommendation: {diagnostic['recommended_approach']}")
            except Exception as e:
                print(f"Error during diagnosis: {str(e)}")

        # Save report
        if diagnostic_reports:
            report_path = os.path.join(
                os.path.dirname(self.processed_files_path),
                f'pdf_diagnostic_report_{self.docs_type}.json'
            )
            try:
                save_json_file(report_path, diagnostic_reports)
                print(f"\nDiagnostic report saved to {report_path}")
            except Exception as e:
                print(f"\nError saving diagnostic report: {str(e)}")

        return diagnostic_reports
