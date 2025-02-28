"""
Tests for Pipeline A main module.
"""

import pytest
from unittest.mock import Mock, patch
from selenium import webdriver
from selenium.webdriver.common.by import By
from a_pipeline.modules.main import (
    check_company_name_in_url,
    check_pdf_url,
    check_url_year,
    find_pdf_in_webpage,
    get_search_results
)

def test_check_company_name_in_url():
    """Test company name detection in URLs."""
    test_cases = [
        ("http://example.com/3M-sustainability-report.pdf", "3M Company", True),
        ("http://example.com/apple-csr-2024.pdf", "Apple Inc", True),
        ("http://example.com/unrelated.pdf", "3M Company", False),
    ]
    
    for url, company, expected in test_cases:
        assert check_company_name_in_url(url, company) == expected

@patch('requests.head')
def test_check_pdf_url(mock_head):
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/report.pdf"
    mock_head.return_value = mock_response

    # Test case where URL is a PDF
    url = "http://example.com/report.pdf"
    assert check_pdf_url(url) == True, f"Failed for URL: {url}, expected True but got False"

    # Test case where URL is not a PDF
    mock_response.url = "http://example.com/report.html"
    url = "http://example.com/report.html"
    assert check_pdf_url(url) == False, f"Failed for URL: {url}, expected False but got True"

    # Test case where request fails
    mock_head.side_effect = Exception("Connection error")
    url = "http://example.com/error.pdf"
    assert check_pdf_url(url) == False, f"Failed for URL: {url}, expected False but got True"

def test_check_url_year():
    # Test case where URL contains matching year
    url = "http://example.com/report-2024.pdf"
    year = 2024
    assert check_url_year(url, year) == True, f"Failed for URL: {url}, year: {year}"

    # Test case where URL contains different year
    url = "http://example.com/report-2023.pdf"
    year = 2024
    assert check_url_year(url, year) == False, f"Failed for URL: {url}, year: {year}"

    # Test case where URL contains no year
    url = "http://example.com/report.pdf"
    year = 2024
    assert check_url_year(url, year) == True, f"Failed for URL: {url}, year: {year}"

@patch('selenium.webdriver.remote.webelement.WebElement')
def test_find_pdf_in_webpage(mock_element):
    # Create a mock driver
    mock_driver = Mock()
    
    # Create mock elements for links
    mock_link1 = Mock()
    mock_link1.get_attribute.side_effect = lambda x: "http://example.com/sustainability-2024.pdf" if x == "href" else None
    mock_link1.text = "Sustainability Report 2024"
    
    mock_link2 = Mock()
    mock_link2.get_attribute.side_effect = lambda x: "http://example.com/annual-report.pdf" if x == "href" else None
    mock_link2.text = "Annual Report 2024"
    
    # Set up mock driver to return our mock links
    mock_driver.find_elements.return_value = [mock_link1, mock_link2]
    
    # Mock check_pdf_url to return True for our test URL
    with patch('a_pipeline.modules.main.check_pdf_url', return_value=True):
        # Test finding a PDF
        result = find_pdf_in_webpage(mock_driver, "Example Corp", "http://example.com", 2024)
        assert isinstance(result, str), "Expected string URL but got None"
        assert "sustainability-2024.pdf" in result, "Expected sustainability report URL"

@patch('selenium.webdriver.Chrome')
def test_get_search_results(mock_driver):
    # Create mock driver instance
    driver = mock_driver.return_value
    
    # Create mock elements
    mock_result1 = Mock()
    mock_result1.text = "Result 1"
    mock_result2 = Mock()
    mock_result2.text = "Result 2"
    
    # Set up mock driver behavior
    driver.get.return_value = None
    driver.find_elements.return_value = [mock_result1, mock_result2]
    
    # Test getting search results
    search_query = (By.CSS_SELECTOR, '.search-result')
    results = get_search_results(driver, "Example Corp", "http://example.com", search_query)
    
    assert results is not None, "Expected search results but got None"
    assert len(results) == 2, "Expected 2 search results"
    assert results[0].text == "Result 1"
    assert results[1].text == "Result 2" 