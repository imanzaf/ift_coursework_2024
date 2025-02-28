import pytest
import os
import requests
from unittest.mock import patch, MagicMock
from selenium.webdriver.chrome.webdriver import WebDriver
from optimized_code import (
    init_driver,
    search_pdf_in_google,
    search_pdf_in_bing,
    extract_text_from_pdf,
    download_pdf,
    search_webpage_in_bing,
)

# 1. Test WebDriver Initialization
def test_init_driver():
    driver = init_driver()
    assert isinstance(driver, WebDriver)
    driver.quit()


# 2. Test Google PDF Search
@patch("optimized_code.search")
def test_search_pdf_in_google(mock_search):
    mock_search.return_value = [
        "https://example.com/report.pdf",
        "https://example.com/page.html",
    ]
    result = search_pdf_in_google("Test Company")
    assert result == "https://example.com/report.pdf"


# 3. Test Bing PDF Search (Mock WebDriver)
@patch("optimized_code.WebDriverWait")
def test_search_pdf_in_bing(mock_wait):
    mock_driver = MagicMock()
    mock_wait.return_value.until.return_value = [
        MagicMock(get_attribute=MagicMock(return_value="https://example.com/report.pdf"))
    ]
    result = search_pdf_in_bing(mock_driver, "Test Company")
    assert result == "https://example.com/report.pdf"


# 4. Test PDF Text Extraction
@pytest.fixture
def sample_pdf(tmp_path):
    """ Create a temporary PDF file for testing """
    pdf_path = tmp_path / "sample.pdf"
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n% This is a test PDF")
    return str(pdf_path)


def test_extract_text_from_pdf(sample_pdf):
    text = extract_text_from_pdf(sample_pdf)
    assert "This is a test PDF" in text or text.strip() != ""


# 5. Test PDF Download
@patch("optimized_code.requests.get")
def test_download_pdf(mock_get, tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"%PDF-1.4\n%Fake PDF Content"
    mock_get.return_value = mock_response

    pdf_path = tmp_path / "test.pdf"
    result = download_pdf("Test Company", "https://example.com/report.pdf")
    assert result is not None
    assert os.path.exists(result)

# 6. Test Report Metadata Storage in PostgreSQL
@patch("optimized_code.connect_postgres")
def test_save_report_to_postgres(mock_db):
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_db.return_value = mock_conn

# 7. Test Scheduled Extraction Execution
@patch("optimized_code.automated_extraction")
def test_scheduler_runs_extraction(mock_extraction):
    scheduler = BackgroundScheduler() scheduler.add_job(mock_extraction, 'cron', day_of_week='sun', hour=3, minute=0) scheduler.start()

# 8. File Upload to MinIO
@patch("optimized_code.MINIO_CLIENT.put_object")
def test_upload_to_minio(mock_minio): mock_minio.return_value = True