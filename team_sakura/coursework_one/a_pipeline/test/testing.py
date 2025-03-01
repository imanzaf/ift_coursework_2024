from datetime import datetime
from team_sakura.coursework_one.a_pipeline.modules.url_parser.extract_year import (
    extract_year_from_url_or_snippet,
)
import yaml
import sqlite3
import pytest
import mongomock
from unittest.mock import patch, mock_open, MagicMock
from minio.error import S3Error


# Mock YAML content to prevent FileNotFoundError
mock_yaml_content1 = """
minio:
  bucket_name: "test_bucket"
  endpoint: "mock_endpoint"
"""

with patch("builtins.open", mock_open(read_data=mock_yaml_content1)):
    with patch("yaml.safe_load", return_value=yaml.safe_load(mock_yaml_content1)):
        from team_sakura.coursework_one.a_pipeline.modules.minio_writer.minio_client import (
            get_minio_client,
            delete_all_files_from_minio,
            upload_to_minio,
            BUCKET_NAME,
        )

# Mock the file reading BEFORE importing the module
mock_yaml_content = """
database:
  mongo_uri: "mongodb://mock_uri"
  mongo_db: "test_db"
  mongo_collection: "test_collection"
"""

with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
    import team_sakura.coursework_one.a_pipeline.modules.db_loader.mongo_db as mongo_db


# Mock YAML configuration before importing the module
mock_yaml_content = """
database:
  sqlite_path: ":memory:"
"""

with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
    with patch(
        "team_sakura.coursework_one.a_pipeline.modules.db_loader.sqlite_loader.config",
        yaml.safe_load(mock_yaml_content),
    ):
        import team_sakura.coursework_one.a_pipeline.modules.db_loader.sqlite_loader as sqlite_loader


@pytest.fixture
def mock_mongo_collection():
    """Fixture to mock MongoDB collection using mongomock."""
    client = mongomock.MongoClient()
    db = client["test_db"]
    collection = db["test_collection"]
    collection.insert_many(
        [
            {"company_name": "Company A", "report_year": 2023},
            {"company_name": "Company B", "report_year": 2022},
        ]
    )
    return collection


@patch(
    "team_sakura.coursework_one.a_pipeline.modules.db_loader.mongo_db.get_mongo_collection"
)
def test_delete_all_documents_from_mongo(
    mock_get_mongo_collection, mock_mongo_collection
):
    """Test deleting all documents from MongoDB."""
    mock_get_mongo_collection.return_value = mock_mongo_collection

    mongo_db.delete_all_documents_from_mongo()
    assert (
        mock_mongo_collection.count_documents({}) == 0
    )  # Ensure documents are deleted


@pytest.fixture
def setup_test_db():
    """Fixture to set up an in-memory SQLite database with test data."""
    conn = sqlite3.connect(":memory:")  # Use in-memory database for testing
    cursor = conn.cursor()

    # Create test table
    cursor.execute(
        """
        CREATE TABLE equity_static (
            security TEXT,
            symbol TEXT,
            gics_sector TEXT,
            gics_industry TEXT,
            country TEXT,
            region TEXT
        )
    """
    )

    # Insert test data
    test_data = [
        ("Company A", "CMPA", "Technology", "Software", "USA", "North America"),
        ("Company B", "CMPB", "Finance", "Banking", "UK", "Europe"),
    ]
    cursor.executemany("INSERT INTO equity_static VALUES (?, ?, ?, ?, ?, ?)", test_data)

    conn.commit()
    yield conn  # Provide the connection to the test function
    conn.close()


def test_extract_year_from_url():
    assert (
        extract_year_from_url_or_snippet("https://example.com/news/2023", "") == "2023"
    )


def test_extract_year_from_snippet():
    assert extract_year_from_url_or_snippet("", "Published in 2021.") == "2021"


def test_extract_year_from_both():
    assert (
        extract_year_from_url_or_snippet(
            "https://example.com/2022/article", "Snippet mentioning 2020"
        )
        == "2022"
    )


def test_no_year_found():
    assert (
        extract_year_from_url_or_snippet("https://example.com", "No year mentioned")
        == "Unknown"
    )
    assert extract_year_from_url_or_snippet("https://example.com/path", "") == "Unknown"


def test_dynamic_year():
    current_year = str(datetime.now().year)
    assert (
        extract_year_from_url_or_snippet(f"https://example.com/{current_year}", "")
        == current_year
    )


@patch("team_sakura.coursework_one.a_pipeline.modules.minio_client.Minio")
def test_get_minio_client(mock_minio):
    """Test MinIO client initialization."""
    mock_client = MagicMock()
    mock_minio.return_value = mock_client
    mock_client.bucket_exists.return_value = True  # Simulate existing bucket

    client = get_minio_client()
    assert client == mock_client
    mock_client.bucket_exists.assert_called_once_with(BUCKET_NAME)


@patch("team_sakura.coursework_one.a_pipeline.modules.minio_client.minio_client")
def test_delete_all_files_from_minio(mock_minio_client):
    """Test deleting all files from MinIO bucket."""
    mock_object = MagicMock()
    mock_object.object_name = "test_file.pdf"
    mock_minio_client.list_objects.return_value = [mock_object]

    delete_all_files_from_minio()
    mock_minio_client.list_objects.assert_called_once_with(BUCKET_NAME, recursive=True)
    mock_minio_client.remove_object.assert_called_once_with(
        BUCKET_NAME, "test_file.pdf"
    )


@patch("team_sakura.coursework_one.a_pipeline.modules.minio_client.minio_client")
def test_delete_all_files_from_minio_error(mock_minio_client):
    """Test handling of S3Error when deleting files from MinIO."""
    mock_minio_client.list_objects.side_effect = S3Error(
        "Error", "Mock error", "RequestID", "HostID"
    )

    with patch("builtins.print") as mock_print:
        delete_all_files_from_minio()
        mock_print.assert_called_with("Error while deleting from Minio: Mock error")


@patch("team_sakura.coursework_one.a_pipeline.modules.minio_client.minio_client")
def test_upload_to_minio(mock_minio_client):
    """Test uploading a file to MinIO."""
    mock_minio_client.fput_object.return_value = None  # Simulate successful upload

    local_pdf_path = "sample.pdf"
    company_symbol = "CMPA"
    report_year = "2023"
    expected_url = f"http://mock_endpoint/{BUCKET_NAME}/{company_symbol}/{report_year}"

    with patch(
        "team_sakura.coursework_one.a_pipeline.modules.minio_client.MINIO_CONFIG",
        {"endpoint": "mock_endpoint"},
    ):
        result = upload_to_minio(local_pdf_path, company_symbol, report_year)

    assert result == expected_url
    mock_minio_client.fput_object.assert_called_once_with(
        BUCKET_NAME, f"{company_symbol}/{report_year}", local_pdf_path
    )
