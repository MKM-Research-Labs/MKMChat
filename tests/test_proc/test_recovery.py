# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/proc/recovery.py."""

import json
import pytest
from unittest.mock import MagicMock, patch

from src.proc.recovery import RecoveryHandler


@pytest.fixture
def recovery_handler(tmp_path):
    """Create a RecoveryHandler with temp paths."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    processed_path = tmp_path / "json" / "processed.json"
    processed_path.parent.mkdir(parents=True, exist_ok=True)

    mock_splitter = MagicMock()
    return RecoveryHandler(
        docs_folder=str(docs_dir),
        text_splitter=mock_splitter,
        docs_type="misc",
        processed_files_path=str(processed_path),
    )


def test_recovery_handles_missing_tracking_file(recovery_handler, tmp_path):
    """RecoveryHandler works even when the processed-files JSON does not exist yet."""
    # Create a dummy file so get_file_hash works
    doc = tmp_path / "docs" / "test.pdf"
    doc.write_bytes(b"%PDF-1.4 fake")

    processed_files = {}

    with patch("src.proc.recovery.get_file_hash", return_value="hash123"):
        result = recovery_handler.handle_problematic_document(
            "test.pdf", processed_files, error_msg="Some generic error"
        )

    # Non-binary error should not trigger recovery, just record failure
    assert result is None
    assert "test.pdf" in processed_files
    assert processed_files["test.pdf"]["status"] == "ERROR_HANDLED"


def test_recovery_handles_corrupted_tracking_file(recovery_handler, tmp_path):
    """RecoveryHandler still works when the tracking file contains corrupt JSON."""
    # Write corrupt JSON to the processed-files path
    processed_path = tmp_path / "json" / "processed.json"
    processed_path.write_text("{invalid json!!")

    doc = tmp_path / "docs" / "test.pdf"
    doc.write_bytes(b"%PDF-1.4 fake")

    # Even though the tracking file is corrupt, handle_problematic_document
    # takes processed_files dict as input (loaded externally), so it still works
    processed_files = {}

    with patch("src.proc.recovery.get_file_hash", return_value="hash456"):
        result = recovery_handler.handle_problematic_document(
            "test.pdf", processed_files, error_msg="Invalid Elementary Object"
        )

    # Binary error detected, recovery attempted
    assert "test.pdf" in processed_files


# ── Additional coverage tests ───────────────────────────────────────────

from langchain_core.documents import Document


class TestIsBinaryError:
    """Tests for _is_binary_error."""

    def test_none_error(self, recovery_handler):
        """None error_msg returns False."""
        assert recovery_handler._is_binary_error(None) is False

    def test_empty_error(self, recovery_handler):
        """Empty string returns False."""
        assert recovery_handler._is_binary_error("") is False

    def test_generic_error(self, recovery_handler):
        """Non-binary error returns False."""
        assert recovery_handler._is_binary_error("File not found") is False

    def test_invalid_elementary_object(self, recovery_handler):
        """'Invalid Elementary Object' triggers binary detection."""
        assert recovery_handler._is_binary_error("Invalid Elementary Object at position 5") is True

    def test_cant_concat_str(self, recovery_handler):
        """ByteStringObject concat error triggers binary detection."""
        assert recovery_handler._is_binary_error("can't concat str to ByteStringObject") is True

    def test_flate_decode(self, recovery_handler):
        """FlateDecode stream filter error triggers binary detection."""
        assert recovery_handler._is_binary_error("stream filter 'FlateDecode' not found") is True


class TestHandleProblematicDocument:
    """Tests for handle_problematic_document."""

    def test_non_binary_error_records_failure(self, recovery_handler, tmp_path):
        """Non-binary error records failure and returns None."""
        doc = tmp_path / "docs" / "test.pdf"
        doc.write_bytes(b"%PDF")

        processed_files = {}
        with patch("src.proc.recovery.get_file_hash", return_value="hash"):
            result = recovery_handler.handle_problematic_document(
                "test.pdf", processed_files, "Generic error"
            )

        assert result is None
        assert processed_files["test.pdf"]["status"] == "ERROR_HANDLED"
        assert processed_files["test.pdf"]["error"] == "Generic error"

    def test_none_error_msg_uses_default(self, recovery_handler, tmp_path):
        """None error_msg uses default message."""
        doc = tmp_path / "docs" / "test.pdf"
        doc.write_bytes(b"%PDF")

        processed_files = {}
        with patch("src.proc.recovery.get_file_hash", return_value="hash"):
            recovery_handler.handle_problematic_document("test.pdf", processed_files, None)

        assert processed_files["test.pdf"]["error"] == "Unknown error during processing"

    def test_binary_error_triggers_recovery(self, recovery_handler, tmp_path):
        """Binary error triggers _attempt_binary_recovery."""
        doc = tmp_path / "docs" / "test.pdf"
        doc.write_bytes(b"%PDF")

        processed_files = {}
        with patch("src.proc.recovery.get_file_hash", return_value="hash"), \
             patch.object(recovery_handler, "_attempt_binary_recovery", return_value=[MagicMock()]) as mock_recover:
            result = recovery_handler.handle_problematic_document(
                "test.pdf", processed_files, "Invalid Elementary Object"
            )

        mock_recover.assert_called_once()
        assert result is not None


class TestAttemptBinaryRecovery:
    """Tests for _attempt_binary_recovery."""

    def test_recovery_success(self, recovery_handler, tmp_path):
        """Successful recovery returns chunks and updates processed_files."""
        doc = tmp_path / "docs" / "test.pdf"
        doc.write_bytes(b"%PDF")

        mock_pages = [
            Document(page_content="Good content", metadata={"source": "test.pdf"})
        ]
        mock_chunks = [MagicMock()]

        processed_files = {"test.pdf": {"error": "original error"}}

        with patch("src.loaders.pdf_loader.EnhancedPDFLoader") as MockLoader:
            MockLoader.return_value.load.return_value = mock_pages
            with patch("src.proc.recovery.sanitize_text", side_effect=lambda t: t), \
                 patch("src.proc.recovery.standardize_metadata", return_value=mock_chunks):
                recovery_handler.text_splitter.split_documents.return_value = mock_chunks
                result = recovery_handler._attempt_binary_recovery(
                    "test.pdf", str(doc), "hash123", processed_files
                )

        assert result is not None
        assert processed_files["test.pdf"]["status"] == "RECOVERED"

    def test_recovery_no_pages(self, recovery_handler, tmp_path):
        """Recovery returns None when loader returns empty list."""
        processed_files = {"test.pdf": {"error": "error"}}

        with patch("src.loaders.pdf_loader.EnhancedPDFLoader") as MockLoader:
            MockLoader.return_value.load.return_value = []
            result = recovery_handler._attempt_binary_recovery(
                "test.pdf", "/fake/test.pdf", "hash", processed_files
            )

        assert result is None

    def test_recovery_skips_error_pages(self, recovery_handler, tmp_path):
        """Recovery skips pages that start with '[Error'."""
        mock_pages = [
            Document(page_content="[Error on page 1]", metadata={"source": "test.pdf"}),
            Document(page_content="Good content", metadata={"source": "test.pdf"})
        ]
        mock_chunks = [MagicMock()]
        processed_files = {"test.pdf": {"error": "error"}}

        with patch("src.loaders.pdf_loader.EnhancedPDFLoader") as MockLoader:
            MockLoader.return_value.load.return_value = mock_pages
            with patch("src.proc.recovery.sanitize_text", side_effect=lambda t: t), \
                 patch("src.proc.recovery.standardize_metadata", return_value=mock_chunks):
                recovery_handler.text_splitter.split_documents.return_value = mock_chunks
                result = recovery_handler._attempt_binary_recovery(
                    "test.pdf", "/fake/test.pdf", "hash", processed_files
                )

        assert result is not None

    def test_recovery_all_error_pages(self, recovery_handler, tmp_path):
        """Recovery returns None when all pages are errors."""
        mock_pages = [
            Document(page_content="[Error on page 1]", metadata={"source": "test.pdf"})
        ]
        processed_files = {"test.pdf": {"error": "error"}}

        with patch("src.loaders.pdf_loader.EnhancedPDFLoader") as MockLoader:
            MockLoader.return_value.load.return_value = mock_pages
            with patch("src.proc.recovery.sanitize_text", side_effect=lambda t: t):
                result = recovery_handler._attempt_binary_recovery(
                    "test.pdf", "/fake/test.pdf", "hash", processed_files
                )

        assert result is None

    def test_recovery_no_chunks_after_split(self, recovery_handler, tmp_path):
        """Recovery returns None when splitting yields no chunks."""
        mock_pages = [
            Document(page_content="Short", metadata={"source": "test.pdf"})
        ]
        processed_files = {"test.pdf": {"error": "error"}}

        with patch("src.loaders.pdf_loader.EnhancedPDFLoader") as MockLoader:
            MockLoader.return_value.load.return_value = mock_pages
            with patch("src.proc.recovery.sanitize_text", side_effect=lambda t: t):
                recovery_handler.text_splitter.split_documents.return_value = []
                result = recovery_handler._attempt_binary_recovery(
                    "test.pdf", "/fake/test.pdf", "hash", processed_files
                )

        assert result is None

    def test_recovery_exception_appends_error(self, recovery_handler, tmp_path):
        """Recovery exception appends error message to processed_files."""
        processed_files = {"test.pdf": {"error": "original error"}}

        with patch("src.loaders.pdf_loader.EnhancedPDFLoader", side_effect=RuntimeError("loader crash")):
            result = recovery_handler._attempt_binary_recovery(
                "test.pdf", "/fake/test.pdf", "hash", processed_files
            )

        assert result is None
        assert "Recovery failed" in processed_files["test.pdf"]["error"]


class TestDiagnoseAndReport:
    """Tests for diagnose_and_report."""

    def test_no_error_files(self, recovery_handler):
        """Returns empty list when no error files exist."""
        result = recovery_handler.diagnose_and_report({"a.pdf": {"status": "SUCCESS"}})
        assert result == []

    def test_file_not_found(self, recovery_handler):
        """Skips files that don't exist on disk."""
        processed_files = {"missing.pdf": {"status": "ERROR"}}
        result = recovery_handler.diagnose_and_report(processed_files)
        assert result == []

    def test_successful_diagnosis(self, recovery_handler, tmp_path):
        """Runs diagnosis and returns reports."""
        doc = tmp_path / "docs" / "bad.pdf"
        doc.write_bytes(b"%PDF")

        mock_diagnostic = {
            "overall_assessment": "problematic",
            "issues_detected": ["binary content"],
            "recommended_approach": "binary_safe"
        }

        processed_files = {"bad.pdf": {"status": "ERROR"}}

        with patch("src.proc.recovery.diagnose_pdf", return_value=mock_diagnostic), \
             patch("src.proc.recovery.save_json_file"):
            result = recovery_handler.diagnose_and_report(processed_files)

        assert len(result) == 1
        assert result[0]["overall_assessment"] == "problematic"

    def test_diagnosis_exception(self, recovery_handler, tmp_path):
        """diagnose_and_report handles exceptions from diagnose_pdf."""
        doc = tmp_path / "docs" / "bad.pdf"
        doc.write_bytes(b"%PDF")

        processed_files = {"bad.pdf": {"status": "ERROR"}}

        with patch("src.proc.recovery.diagnose_pdf", side_effect=RuntimeError("diagnosis failed")):
            result = recovery_handler.diagnose_and_report(processed_files)

        assert result == []

    def test_save_report_failure(self, recovery_handler, tmp_path):
        """diagnose_and_report handles save failure gracefully."""
        doc = tmp_path / "docs" / "bad.pdf"
        doc.write_bytes(b"%PDF")

        mock_diagnostic = {
            "overall_assessment": "ok",
            "issues_detected": [],
            "recommended_approach": "standard"
        }

        processed_files = {"bad.pdf": {"status": "ERROR"}}

        with patch("src.proc.recovery.diagnose_pdf", return_value=mock_diagnostic), \
             patch("src.proc.recovery.save_json_file", side_effect=OSError("save failed")):
            result = recovery_handler.diagnose_and_report(processed_files)

        # Should still return results despite save failure
        assert len(result) == 1
