import pytest
import psycopg2
import subprocess
import sys
import os
from minio import Minio

# Dynamically add the path to the source files
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../modules")))

from config import DB_CONFIG, MINIO_CONFIG
from minio_client import get_db_connection, upload_to_minio, update_minio_path, get_pdfs_to_download

def test_database_connection():
    """Test if the database connection is successful."""
    conn = get_db_connection()
    assert conn is not None, "❌ Database connection failed!"
    conn.close()
    print("✅ Database connection successful.")

def test_minio_connection():
    """Test if MinIO connection is successful."""
    try:
        minio_client = Minio(
            MINIO_CONFIG["endpoint"],
            access_key=MINIO_CONFIG["access_key"],
            secret_key=MINIO_CONFIG["secret_key"],
            secure=False
        )
        assert minio_client is not None, "❌ MinIO connection failed!"
        print("✅ MinIO connection successful.")
    except Exception as e:
        pytest.fail(f"❌ MinIO connection error: {e}")

def test_minio_bucket():
    """Test if the specified MinIO bucket exists."""
    minio_client = Minio(
        MINIO_CONFIG["endpoint"],
        access_key=MINIO_CONFIG["access_key"],
        secret_key=MINIO_CONFIG["secret_key"],
        secure=False
    )

    bucket_name = MINIO_CONFIG["bucket"]
    found = minio_client.bucket_exists(bucket_name)
    assert found, f"❌ MinIO bucket '{bucket_name}' does not exist!"
    print(f"✅ MinIO bucket '{bucket_name}' exists.")

def test_file_upload():
    """Test uploading a file to MinIO and verifying its existence."""
    minio_client = Minio(
        MINIO_CONFIG["endpoint"],
        access_key=MINIO_CONFIG["access_key"],
        secret_key=MINIO_CONFIG["secret_key"],
        secure=False
    )

    test_file = "test_upload.pdf"
    bucket_name = MINIO_CONFIG["bucket"]
    object_name = "test_folder/test_upload.pdf"

    # Create test file
    with open(test_file, "w") as f:
        f.write("Test PDF content.")

    # Upload file
    upload_to_minio(test_file, bucket_name, object_name)

    # Verify file exists in MinIO
    found = minio_client.stat_object(bucket_name, object_name)
    assert found is not None, "❌ Uploaded file not found in MinIO!"

    # Cleanup
    minio_client.remove_object(bucket_name, object_name)
    os.remove(test_file)
    print("✅ File upload & verification successful.")

def test_update_minio_path():
    """Test if `update_minio_path()` correctly updates the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert a test record
    cursor.execute("""
        INSERT INTO ginkgo.csr_reports (symbol, company_name, report_year, minio_path)
        VALUES ('TEST', 'Test Company', 2024, NULL)
        ON CONFLICT (symbol, report_year) DO NOTHING;
    """)
    conn.commit()

    # Run update function
    update_minio_path("TEST", 2024, "s3://test-bucket/test_upload.pdf")

    # Verify database update
    cursor.execute("""
        SELECT minio_path FROM ginkgo.csr_reports WHERE symbol = 'TEST' AND report_year = 2024;
    """)
    updated_path = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    assert updated_path == "s3://test-bucket/test_upload.pdf", "❌ Database update failed!"
    print("✅ Database minio_path update successful.")

def test_pdfs_to_download():
    """Test if PDFs needing processing can be retrieved."""
    pdfs = get_pdfs_to_download()
    assert isinstance(pdfs, list), "❌ Expected list of PDFs, got something else."
    print(f"✅ {len(pdfs)} PDFs found for processing.")

def test_code_quality():
    """Run linting, formatting, and security scans for minio_client.py only."""
    python_exec = sys.executable  # Get the correct Python path
    minio_client_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../modules/minio_client.py"))

    print("🔍 Running flake8 on minio_client.py...")
    subprocess.run([python_exec, "-m", "flake8", minio_client_path, "--max-line-length=100"], check=True)

    print("🔍 Checking code formatting with black...")
    subprocess.run([python_exec, "-m", "black", "--check", minio_client_path], check=True)

    print("🔍 Sorting imports with isort...")
    subprocess.run([python_exec, "-m", "isort", "--check-only", minio_client_path], check=True)

    print("🔍 Running security scans with Bandit...")
    subprocess.run([python_exec, "-m", "bandit", "-r", minio_client_path], check=True)

if __name__ == "__main__":
    test_database_connection()
    test_minio_connection()
    test_minio_bucket()
    test_file_upload()
    test_update_minio_path()
    test_pdfs_to_download()
    test_code_quality()
