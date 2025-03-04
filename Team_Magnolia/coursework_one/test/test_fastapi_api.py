import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from modules.api.fastapi_api import app, collection_reports, MINIO_HOST, MINIO_BUCKET

# 创建测试客户端
client = TestClient(app)


# -------------------------------
# 1️⃣ 测试 MongoDB 连接
# -------------------------------
@patch("modules.api.fastapi_api.MongoClient")
def test_mongodb_connection(mock_mongo_client):
    """测试 MongoDB 连接是否成功"""
    mock_db = MagicMock()
    mock_mongo_client.return_value = mock_db

    assert mock_mongo_client.called


# -------------------------------
# 2️⃣ 测试 CSR 报告查询 API
# -------------------------------
@patch("modules.api.fastapi_api.collection_reports.find")
def test_get_reports(mock_find):
    """测试 CSR 报告查询"""
    mock_find.return_value = [
        {
            "company_name": "Test Corp",
            "csr_report_url": "http://example.com/test.pdf",
            "storage_path": "2023/Test_Corp.pdf",
            "csr_report_year": 2023,
            "ingestion_time": "2025-02-27T00:00:00",
        }
    ]

    response = client.get("/reports?company=Test&year=2023")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["company_name"] == "Test Corp"
    assert data[0]["download_link"] == f"http://{MINIO_HOST}:9000/{MINIO_BUCKET}/2023/Test_Corp.pdf"


# -------------------------------
# 3️⃣ 测试未找到数据时的情况
# -------------------------------
@patch("modules.api.fastapi_api.collection_reports.find")
def test_get_reports_not_found(mock_find):
    """测试查询无结果时的响应"""
    mock_find.return_value = []

    response = client.get("/reports?company=NonExistent&year=2023")
    assert response.status_code == 404
    assert response.json()["detail"] == "No reports found for the given query"


# -------------------------------
# 4️⃣ 测试批量下载 API
# -------------------------------
@patch("modules.api.fastapi_api.shutil.make_archive")
@patch("modules.api.fastapi_api.os.makedirs")
@patch("modules.api.fastapi_api.os.path.exists", return_value=True)
@patch("modules.api.fastapi_api.shutil.rmtree")
def test_download_reports(
    mock_rmtree, mock_exists, mock_makedirs, mock_make_archive
):
    """测试批量下载 CSR 报告"""
    request_data = {
        "report_paths": ["2023/Test_Corp.pdf", "2023/Another_Corp.pdf"]
    }
    response = client.post("/download-zip", json=request_data)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


# -------------------------------
# 5️⃣ 测试批量下载 - 无文件时返回 400
# -------------------------------
def test_download_reports_no_files():
    """测试批量下载时未选择文件"""
    request_data = {"report_paths": []}
    response = client.post("/download-zip", json=request_data)

    assert response.status_code == 400
    assert response.json()["detail"] == "No reports selected for download"


# -------------------------------
# 6️⃣ 测试异常处理
# -------------------------------
@patch("modules.api.fastapi_api.collection_reports.find", side_effect=Exception("Database Error"))
def test_get_reports_exception(mock_find):
    """测试查询时发生异常"""
    response = client.get("/reports?company=ErrorTest&year=2023")

    assert response.status_code == 500
    assert "Database Error" in response.json()["detail"]
