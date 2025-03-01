import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime

# import modules
from ..modules.crawler.crawler import (
    init_driver,
    download_pdf,
    is_pdf_contains_keywords,
    get_search_results,
    process_company,
    search_webpage_in_bing,
    find_pdf_in_webpage
)
from ..modules.crawler.google_api_combined_crawler import (
    _get_report_search_results,
    _score_esg_report,
    score_text,
    score_year,
    _sort_search_results
)
from ..modules.crawler.sustainability_reports_beautifulsoup import (
    fetch_reports,
    store_reports_for_company
)

# test basic crawler (crawler.py)
class TestBasicCrawler:
    def test_init_driver(self):
        with patch('selenium.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            driver = init_driver()
            assert driver == mock_driver
            mock_chrome.assert_called_once()

    def test_is_pdf_contains_keywords(self):
        test_pdf_path = "test.pdf"
        
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            # test case 1: contains keywords
            mock_page.extract_text.return_value = "scope 1 emissions data 2024 esg report"
            mock_reader.return_value.pages = [mock_page]
            
            assert is_pdf_contains_keywords(test_pdf_path) == True
            
            # test case 2: not contains keywords
            mock_page.extract_text.return_value = "annual financial report 2024"
            assert is_pdf_contains_keywords(test_pdf_path) == False

    def test_download_pdf(self):
        with patch('requests.get') as mock_get, \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"PDF content"
            mock_get.return_value = mock_response
            
            with patch('crawler.is_pdf_contains_keywords', return_value=True):
                result = download_pdf("TestCompany", "http://test.com/report.pdf")
                assert result == "./reports/TestCompany.pdf"

    def test_get_search_results(self):
        mock_driver = Mock()
        mock_wait = Mock()
        mock_element = Mock()
        
        with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
            mock_wait.until.return_value = [mock_element]
            
            results = get_search_results(
                mock_driver,
                "TestCompany",
                "http://test.com",
                ("css", "selector")
            )
            assert results == [mock_element]

    def test_process_company(self):
        with patch('crawler.init_driver') as mock_init_driver, \
             patch('crawler.search_webpage_in_bing') as mock_search, \
             patch('crawler.find_pdf_in_webpage') as mock_find_pdf, \
             patch('crawler.is_valid_esg_report_from_url', return_value=True):
            
            mock_driver = Mock()
            mock_init_driver.return_value = mock_driver
            mock_search.return_value = ["http://test.com"]
            mock_find_pdf.return_value = "http://test.com/report.pdf"
            
            result = process_company("TestCompany")
            assert result == ("http://test.com", "http://test.com/report.pdf")

# test Google API crawler (google_api_combined_crawler.py)
class TestGoogleApiCrawler:
    def test_get_report_search_results(self):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [{
                    "link": "http://test.com/report.pdf",
                    "title": "ESG Report 2024",
                    "snippet": "Sustainability Report",
                    "pagemap": {"metatags": [{"creationdate": "2024"}]}
                }]
            }
            mock_get.return_value = mock_response
            
            with patch('team_adansonia.coursework_one.a_link_retrieval.modules.validation.validation.validate_esg_report', return_value=True):
                result = _get_report_search_results("TestCompany", "TEST", "2024")
                assert result == "http://test.com/report.pdf"

    def test_score_text(self):
        test_text = "esg sustainability report environmental governance"
        score = score_text(test_text)
        assert score > 0

    def test_score_year(self):
        test_text = "report 2024 sustainability"
        score = score_year(test_text, "2024")
        assert score > 0
        
        test_text = "report 2023 sustainability"
        score = score_year(test_text, "2024")
        assert score < 0

# test BeautifulSoup crawler (sustainability_reports_beautifulsoup.py)
class TestBeautifulSoupCrawler:
    def test_fetch_reports(self):
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.text = """
                <html>
                    <div class="companyName"><a href="/company/test">TestCompany</a></div>
                    <div class="vendor_name"><div class="heading">TestCompany</div></div>
                    <div class="most_recent_content_block">
                        <div class="bold_txt">ESG Report 2024</div>
                        <div class="view_btn"><a href="/report.pdf">View</a></div>
                    </div>
                </html>
            """
            mock_post.return_value = mock_response
            
            result = fetch_reports("TestCompany")
            assert "2024" in result
            assert result["2024"].endswith("report.pdf")

    def test_store_reports_for_company(self):
        with patch('sustainability_reports_beautifulsoup.fetch_reports') as mock_fetch:
            mock_fetch.return_value = {
                "2024": "http://test.com/report2024.pdf",
                "2023": "http://test.com/report2023.pdf"
            }
            
            result = store_reports_for_company("TestCompany", "TEST")
            assert "2024" in result
            assert "2023" in result

# test error handling
class TestErrorHandling:
    def test_invalid_url(self):
        result = download_pdf("TestCompany", "invalid_url")
        assert result is None
    
    def test_failed_pdf_download(self):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            result = download_pdf("TestCompany", "http://test.com/report.pdf")
            assert result is None

    def test_company_not_found(self):
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.text = "<html></html>"
            mock_post.return_value = mock_response
            
            result = fetch_reports("NonexistentCompany")
            assert "error" in result

if __name__ == '__main__':
    pytest.main(['-v']) 