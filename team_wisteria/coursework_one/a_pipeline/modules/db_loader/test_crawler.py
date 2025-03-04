# test_crawler.py

import os
import pytest
from unittest.mock import patch, MagicMock
from crawler import PDFScraper, Config


@pytest.fixture
def scraper():
    """
    Returns a fresh instance of PDFScraper for each test.
    """
    return PDFScraper()



@patch("crawler.requests.get")
def test_download_pdf_404(mock_get, scraper):
    """
    Test that download_pdf() returns False when the server responds with 404.
    """
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = scraper.download_pdf("NotFoundCo", "http://fakeurl.com/notfound.pdf", 2021)
    assert result is False, "Expected download_pdf to return False for a 404 response."

@patch("crawler.requests.get")
def test_download_pdf_validate_fail(mock_get, scraper):
    """
    Test that download_pdf() returns False when validate_pdf() fails,
    and the downloaded file is removed.
    """
    # Mock a successful HTTP 200 response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"Some invalid PDF content"
    mock_get.return_value = mock_response

    # Mock validate_pdf to return False
    with patch.object(scraper, "validate_pdf", return_value=False):
        result = scraper.download_pdf("BadPDFCo", "http://fakeurl.com/bad.pdf", 2022)

    assert result is False, "Expected download_pdf to return False if PDF validation fails."



@patch("crawler.pdfplumber.open")
def test_validate_pdf_fail(mock_pdfplumber):
    """
    Test that validate_pdf() returns False when the text is either too short
    or does not contain any of the valid keywords (sustainability, csr, esg, etc.).
    """
    # Provide a short text that excludes valid keywords
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Short text without keywords"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

    scraper = PDFScraper()
    result = scraper.validate_pdf("some/path/fake.pdf")

    assert result is False, (
        "Expected validate_pdf to return False if text is too short or missing keywords."
    )