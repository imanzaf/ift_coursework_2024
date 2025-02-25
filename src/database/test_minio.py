# test_minio.py
import sys
import os
from loguru import logger

# Add coursework_one directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Now import MinioFileSystem
from src.database.minio_utils import MinioFileSystem

def main():
    logger.info("Testing MinioFileSystem...")

    # Instantiate your MinioFileSystem
    minio_fs = MinioFileSystem()

    # 1. Create bucket if not exists
    minio_fs.create_bucket(minio_fs.bucket_name)

    # 2. Upload a local PDF
    local_pdf = "test_report.pdf"  # Ensure this file exists in your local dir
    company_id = "123"
    year = "2024"
    logger.info("Uploading a PDF to MinIO...")
    object_name = minio_fs.upload_pdf(local_pdf, company_id, year)
    logger.info(f"Uploaded object name: {object_name}")

    # 3. Generate a presigned URL for viewing
    presigned_url = minio_fs.view_pdf(object_name, expiry_hours=2)
    logger.info(f"Presigned URL (view_pdf): {presigned_url}")

    # 4. Download the file back
    download_dest = "downloaded_test_report.pdf"
    minio_fs.download_file(object_name, download_dest)
    logger.info(f"Downloaded file to: {download_dest}")

    # 5. List files by company
    files_for_company = minio_fs.list_files_by_company(company_id)
    logger.info(f"List of files for company {company_id}: {files_for_company}")

if __name__ == "__main__":
    main()
