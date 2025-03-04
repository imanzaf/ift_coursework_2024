import pytest
import os
import datetime
from unittest.mock import patch, MagicMock
from modules.scraper.csr_scraper import (
    write_log,
    init_driver,
    get_search_results,
    download_pdf,
    upload_to_minio,
    save_csr_report_info_to_mongo,
    get_company_list_from_postgres,
)

# -------------------------------
# 1️⃣ 测试日志写入功能
# -------------------------------
def test_write_log():
    log_file = "test_log.log"
    message = "Test log message"
    
    write_log(message)

    # 检查日志文件是否存在
    assert os.path.exists(log_file)

    # 检查日志内容
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert message in content

    # 清理测试日志文件
    os.remove(log_file)


# -------------------------------
# 2️⃣ 测试 ChromeDriver 初始化
# -------------------------------
@patch("modules.scraper.csr_scraper.webdriver.Chrome")
@patch("modules.scraper.csr_scraper.chromedriver_autoinstaller.install")
def test_init_driver(mock_install, mock_chrome):
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver

    driver = init_driver()
    
    assert driver is not None
    mock_install.assert_called_once()
    mock_chrome.assert_called_once()


# -------------------------------
# 3️⃣ 测试 Bing 搜索功能
# -------------------------------
@patch("modules.scraper.csr_scraper.get_search_results")
def test_get_search_results(mock_get_results):
    mock_driver = MagicMock()
    mock_results = [MagicMock(), MagicMock()]
    mock_get_results.return_value = mock_results

    results = get_search_results(mock_driver, "Test Query")

    assert len(results) == 2
    mock_get_results.assert_called_once()


# -------------------------------
# 4️⃣ 测试 PDF 下载
# -------------------------------
@patch("modules.scraper.csr_scraper.requests.get")
def test_download_pdf(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"%PDF-1.4 Test PDF content"
    mock_get.return_value = mock_response

    file_path = download_pdf("Test Company", 2023, "http://example.com/test.pdf")

    assert file_path is not None
    assert os.path.exists(file_path)

    os.remove(file_path)  # 清理测试文件


# -------------------------------
# 5️⃣ 测试 MinIO 上传
# -------------------------------
@patch("modules.scraper.csr_scraper.MINIO_CLIENT.put_object")
def test_upload_to_minio(mock_put_object):
    test_file = "test.pdf"
    with open(test_file, "wb") as f:
        f.write(b"Test file content")

    object_name = upload_to_minio("Test Company", 2023, test_file)

    assert object_name is not None
    assert object_name == "2023/Test Company.pdf"
    mock_put_object.assert_called_once()

    os.remove(test_file)  # 清理测试文件


# -------------------------------
# 6️⃣ 测试 MongoDB 数据存储
# -------------------------------
@patch("modules.scraper.csr_scraper.mongo_db")
def test_save_csr_report_info_to_mongo(mock_mongo_db):
    mock_collection = MagicMock()
    mock_mongo_db.__getitem__.return_value = mock_collection

    save_csr_report_info_to_mongo("Test Company", "http://example.com/test.pdf", "2023/Test Company.pdf", 2023)

    mock_collection.update_one.assert_called_once()


# -------------------------------
# 7️⃣ 测试 PostgreSQL 获取公司列表
# -------------------------------
@patch("modules.scraper.csr_scraper.psycopg2.connect")
def test_get_company_list_from_postgres(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("Company A",), ("Company B",)]
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    companies = get_company_list_from_postgres()

    assert len(companies) == 2
    assert "Company A" in companies
    assert "Company B" in companies

    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()
