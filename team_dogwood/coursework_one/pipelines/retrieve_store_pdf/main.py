"""

This script retrieves CSR (Corporate Social Responsibility) report URLs from
a PostgreSQL database (table: csr_reporting.company_csr_reports), then
immediately downloads and stores the PDFs in MinIO—bypassing any local disk usage.

Usage:

Implementation Overview:
    1) We query the 'company_csr_reports' table for all rows matching the specified company ID.
    2) For each row, we:
       - Read the PDF URL from 'report_url'
       - Stream-download the PDF in memory (requests + BytesIO)
       - Upload the PDF bytes directly to MinIO (via minio_utils.MinioFileSystem)
    3) If the PDF is unavailable or the URL fails, the script logs a warning and continues with the next row.

Note:
    - "retrieve_store_url" script, it likely populates
      'csr_reporting.company_csr_reports' with the relevant 'report_url' fields.
    - We need to ensure that script uses the same table and columns.

"""

import io
import os
import sys
from typing import List

import requests
from loguru import logger

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.database.minio import MinioFileSystem

# Ensure correct references to your DB and MinIO modules
from src.database.postgres import PostgreSQLDB


def fetch_csr_reports_by_company(company_id: int) -> List[dict]:
    """
    Fetch all CSR report metadata (URLs, years, etc.) for a given company ID
    from our PostgreSQL database.

    Args:
        company_id (int): The unique ID of the company in the DB.

    Returns:
        List[dict]: Each dict includes fields like 'report_url' and 'report_year'.
                    Example: [{'report_url': 'https://example.com/report.pdf',
                               'report_year': 2024,
                               ...}, ...]
    """
    with PostgreSQLDB() as db:
        results = db.get_csr_reports_by_company(company_id)
        logger.info(f"Found {len(results)} report(s) for company={company_id}")
    return results


def retrieve_and_store_pdf(company_id: int) -> None:
    """
    Main pipeline function that:
      1) Queries the DB for all CSR URLs for 'company_id'.
      2) Downloads each PDF in-memory.
      3) Uploads each PDF to MinIO (via MinioFileSystem) without saving to disk.

    Args:
        company_id (int): The DB ID of the company whose CSR reports we want to process.

    Workflow Steps:
        a) 'fetch_csr_reports_by_company(company_id)'
        b) For each row, do requests.get(...) chunked into BytesIO
        c) 'minio_fs.write_pdf_bytes(...)' with the in-memory PDF

    Potential Edge Cases:
        - If 'report_url' is invalid or the server returns an error code, we log a warning and skip it.
        - If the DB has no records for that company, the script logs a warning and exits gracefully.
    """
    # 1. Fetch all relevant DB records
    records = fetch_csr_reports_by_company(company_id)
    if not records:
        logger.warning(
            f"No CSR report URLs found for company_id={company_id}. Exiting."
        )
        return

    # 2. Initialize the MinIO filesystem wrapper
    minio_fs = MinioFileSystem()

    for rec in records:
        report_url = rec["report_url"]
        report_year = str(rec["report_year"])  # e.g., '2024'

        # Derive a filename from the URL or fallback
        file_name = report_url.split("/")[-1] or "report.pdf"

        logger.info(f"Attempting to download PDF from: {report_url}")
        try:
            # Stream-download to in-memory buffer
            response = requests.get(report_url, stream=True, timeout=15)
            if response.status_code != 200:
                logger.warning(
                    f"Failed to download {report_url} (status={response.status_code})"
                )
                continue

            pdf_buffer = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_buffer.write(chunk)

            # Reset buffer pointer and read
            pdf_buffer.seek(0)
            pdf_data = pdf_buffer.read()

        except Exception as e:
            logger.error(f"Error downloading {report_url}: {e}")
            continue

        # 3. Upload the PDF bytes to MinIO
        logger.info(
            f"Uploading '{file_name}' for company={company_id}, year={report_year} to MinIO..."
        )
        try:
            object_name = minio_fs.write_pdf_bytes(
                pdf_bytes=pdf_data,
                company_id=str(company_id),
                report_year=report_year,
                file_name=file_name,
            )
            logger.info(f"Successfully uploaded to MinIO path: {object_name}")
        except Exception as e:
            logger.error(f"Error uploading to MinIO: {e}")


def main() -> None:
    """
    Example driver code. In a production setting, you might:
     - Parse 'company_id' from CLI arguments or config
     - Possibly loop over multiple companies

    Usage:
        poetry run python retrieve_store_pdf.py
    """
    logger.info("Starting the 'retrieve_store_pdf' pipeline...")

    example_company_id = 1
    retrieve_and_store_pdf(example_company_id)

    logger.info("Pipeline completed.")


if __name__ == "__main__":
    main()
