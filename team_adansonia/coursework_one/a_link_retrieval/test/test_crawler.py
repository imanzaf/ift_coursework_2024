import pytest
from unittest.mock import Mock, patch
import os
from datetime import datetime

# 导入被测试的模块
from crawler import (
    init_driver,
    download_pdf,
    is_pdf_contains_keywords,
    get_search_results,
    process_company
)
from crawler_google_api import _get_report_search_results, SearchResult

# 测试初始化WebDriver
def test_init_driver():
    with patch('crawler.webdriver.Chrome') as mock_chrome:
        # 模拟driver初始化
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        driver = init_driver()
        
        # 验证Chrome被正确初始化
        assert driver == mock_driver
        mock_chrome.assert_called_once()

# 测试PDF关键词检查功能
def test_is_pdf_contains_keywords():
    # 创建测试用的PDF文件路径
    test_pdf_path = "test.pdf"
    
    # 模拟PdfReader
    with patch('crawler.PdfReader') as mock_reader:
        # 设置模拟的PDF内容
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is a test document with scope 1 emissions data for 2024"
        mock_reader.return_value.pages = [mock_page]
        
        # 测试包含关键词的情况
        result = is_pdf_contains_keywords(test_pdf_path)
        assert result == True
        
        # 测试不包含关键词的情况
        mock_page.extract_text.return_value = "This is a test document without relevant keywords"
        result = is_pdf_contains_keywords(test_pdf_path)
        assert result == False

# 测试PDF下载功能
def test_download_pdf():
    with patch('crawler.requests.get') as mock_get:
        # 模拟成功的HTTP响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"PDF content"
        mock_get.return_value = mock_response
        
        # 模拟PDF内容验证
        with patch('crawler.is_pdf_contains_keywords', return_value=True):
            result = download_pdf("TestCompany", "http://test.com/report.pdf")
            assert result == "./reports/TestCompany.pdf"
            
            # 清理测试文件
            if os.path.exists("./reports/TestCompany.pdf"):
                os.remove("./reports/TestCompany.pdf")

# 测试搜索结果获取功能
def test_get_search_results():
    with patch('crawler.WebDriverWait') as mock_wait:
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait.return_value.until.return_value = [mock_element]
        
        results = get_search_results(
            mock_driver,
            "TestCompany",
            "http://test.com",
            ("css", "selector")
        )
        
        assert results == [mock_element]

# 测试Google API搜索功能
def test_get_report_search_results():
    with patch('crawler_google_api.requests.get') as mock_get:
        # 模拟API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{
                "link": "http://test.com/report.pdf",
                "title": "Sustainability Report 2024",
                "snippet": "ESG Report"
            }]
        }
        mock_get.return_value = mock_response
        
        result = _get_report_search_results("TestCompany", "TEST", "2024")
        assert result == "http://test.com/report.pdf"

# 测试SearchResult评分功能
def test_search_result_scoring():
    search_result = SearchResult(
        company_name="TestCompany",
        ticker="TEST",
        url="http://testcompany.com/sustainability-report-2024.pdf",
        title="TestCompany Sustainability Report 2024",
        description="ESG and Sustainability Report",
        year="2024"
    )
    
    score = search_result.score_search()
    assert score > 0

# 测试完整的公司处理流程
def test_process_company():
    with patch('crawler.init_driver') as mock_init_driver:
        mock_driver = Mock()
        mock_init_driver.return_value = mock_driver
        
        # 模拟网页搜索结果
        with patch('crawler.search_webpage_in_bing') as mock_search:
            mock_search.return_value = ["http://test.com"]
            
            # 模拟PDF查找
            with patch('crawler.find_pdf_in_webpage') as mock_find_pdf:
                mock_find_pdf.return_value = "http://test.com/report.pdf"
                
                result = process_company("TestCompany")
                assert result == ("http://test.com", "http://test.com/report.pdf")

# 测试错误处理
def test_error_handling():
    # 测试无效URL的情况
    result = download_pdf("TestCompany", "invalid_url")
    assert result is None
    
    # 测试无效PDF的情况
    with patch('crawler.requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection error")
        result = download_pdf("TestCompany", "http://test.com/report.pdf")
        assert result is None

if __name__ == '__main__':
    pytest.main(['-v']) 