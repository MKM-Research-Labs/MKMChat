# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Temporary directory and sample file fixtures."""

import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary directory pre-populated with the subdirs MKMChat expects."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "faiss").mkdir()
    (tmp_path / "json").mkdir()
    (tmp_path / "templates").mkdir()
    (tmp_path / "static").mkdir()
    return tmp_path


@pytest.fixture
def temp_chats_file(temp_data_dir):
    """Create an empty chats JSON file in the temp directory."""
    chats_file = temp_data_dir / "json" / "all_chats.json"
    chats_file.write_text(json.dumps({"chats": []}, indent=2))
    return str(chats_file)


@pytest.fixture
def sample_pdf_file(temp_data_dir):
    """Create a minimal valid PDF file for loader tests.

    This is a bare-bones PDF that most parsers can handle.
    """
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (Test document) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"0000000360 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n441\n%%EOF\n"
    )
    docs_dir = temp_data_dir / "docs"
    pdf_path = docs_dir / "test_document.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def sample_text_file(temp_data_dir):
    """Create a simple text file (not a supported doc format)."""
    txt_path = temp_data_dir / "docs" / "readme.txt"
    txt_path.write_text("This is a plain text file, not supported for ingestion.")
    return txt_path
