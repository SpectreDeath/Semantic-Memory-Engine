"""
Basic tests for SME OCR Service.
Note: Full OCR testing requires actual image/PDF files and PaddleOCR models.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint():
    """Test health check endpoint returns expected structure."""
    # This is a placeholder - actual test requires running app
    # Import would fail if PaddleOCR isn't installed
    pass


def test_ocr_response_schema():
    """Test OCR response matches expected schema."""
    # This is a placeholder - actual test requires running app
    pass


@pytest.mark.skip(reason="Requires PaddleOCR models and test files")
def test_ocr_image():
    """Test OCR on a sample image."""
    pass


@pytest.mark.skip(reason="Requires PaddleOCR models and test files")
def test_ocr_pdf():
    """Test OCR on a sample PDF."""
    pass
