"""
Tests for the MinIO upload module.
"""

import os
import pytest
import boto3
import psycopg2
from unittest.mock import Mock, patch, mock_open
from upload_to_minio import (
    get_config,
    create_minio_client,
    sanitize_name,
    insert_into_db,
    upload_to_minio
)

def test_get_config():
    """Test configuration retrieval."""
    config = get_config()
    assert isinstance(config, dict)
    assert 'minio' in config
    assert 'postgres' in config
    assert 'source_csv_path' in config
    assert 'local_folder' in config

def test_sanitize_name():
    """Test name sanitization function."""
    test_cases = [
        ("Test Company", "Test_Company"),
        ("Test, Inc.", "Test_Inc"),
        ("Test's Corp", "Tests_Corp"),
    ]
    
    for input_name, expected in test_cases:
        assert sanitize_name(input_name) == expected

@pytest.mark.parametrize("file_exists", [True, False])
@patch('boto3.client')
@patch('os.path.exists')
def test_upload_to_minio(mock_exists, mock_boto3, file_exists, tmp_path):
    """Test MinIO upload functionality."""
    # Setup
    config = {
        'minio': {
            'endpoint': 'http://localhost:9000',
            'bucket_name': 'test-bucket'
        }
    }
    mock_client = Mock()
    mock_boto3.return_value = mock_client
    mock_exists.return_value = file_exists
    
    # Create test file path
    file_path = os.path.join(tmp_path, "Test Company_2024.pdf")
    security = "Test Company"
    report_year = 2024
    
    if file_exists:
        # Test successful upload
        upload_to_minio(config, mock_client, file_path, security, report_year)
        
        # Verify MinIO upload was called
        mock_client.upload_file.assert_called_once_with(
            file_path,
            'test-bucket',
            'Test_Company/2024/Test Company_2024.pdf'
        )
    else:
        # Test file not found case
        with pytest.raises(FileNotFoundError):
            upload_to_minio(config, mock_client, file_path, security, report_year)

@patch('psycopg2.connect')
def test_insert_into_db(mock_connect):
    """Test database insertion functionality."""
    # Setup mock cursor and connection
    mock_cursor = Mock()
    mock_conn = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    
    # Test data
    config = {
        'postgres': {
            'host': 'localhost',
            'port': '5439',
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
    }
    security = "Test Company"
    report_year = 2024
    minio_url = "http://localhost:9000/test-bucket/Test_Company/2024/test.pdf"
    source_url = "http://example.com/report.pdf"
    
    # Call function
    insert_into_db(config, security, report_year, minio_url, source_url)
    
    # Verify database operations
    assert mock_cursor.execute.call_count >= 3  # Schema creation, table creation, and insert
    mock_conn.commit.assert_called()
    mock_conn.close.assert_called_once() 