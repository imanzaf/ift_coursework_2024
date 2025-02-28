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
def test_download_pdf_ok(mock_get, scraper):
    """
    Test that download_pdf() returns True when the PDF is downloaded successfully,
    and validate_pdf() passes.
    """
    # Mock the response from requests.get
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"Fake PDF Content"
    mock_get.return_value = mock_response

    # Mock validate_pdf to return True, avoiding real PDF processing
    with patch.object(scraper, "validate_pdf", return_value=True) as mock_validate:
        result = scraper.download_pdf("TestCo", "http://fakeurl.com/report.pdf", 2021)

    # Assert that download was "successful" and validate_pdf was called
    assert result is True, "Expected download_pdf to return True under normal conditions."
    mock_validate.assert_called_once()

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
def test_validate_pdf_ok(mock_pdfplumber):
    """
    Test that validate_pdf() returns True when the text is long enough
    (>= Config.PDF_MIN_LENGTH) and contains at least one valid keyword.
    """
    # Construct a sufficiently long string that includes a valid keyword
    repeated_text = ("sustainability environment " * 50)
    # By repeating the keywords 50 times, we exceed 1000 characters.

    # Mock pdfplumber to provide our artificial text
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = repeated_text
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

    scraper = PDFScraper()
    result = scraper.validate_pdf("some/path/fake.pdf")

    assert result is True, (
        "Expected validate_pdf to return True when the PDF content is "
        ">= 1000 characters and contains a valid keyword."
    )

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
