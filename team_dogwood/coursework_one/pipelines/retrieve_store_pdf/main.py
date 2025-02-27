"""
Retrieves each row from csr_reporting.company_csr_reports and downloads/stores
the PDF in MinIO. Bypasses local storage by streaming to memory.

"""

import io
import os
import sys
from typing import List

import requests
from loguru import logger

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.data_models.company import Company, ESGReport
from src.database.minio import MinioFileSystem
from src.database.postgres import PostgreSQLDB


def get_all_report_urls(db: PostgreSQLDB) -> List[dict]:
    """
    Get all report urls from the database.

    NOTE - function currently reads each row into a separate data model (even if there are multiple rows for the same company).
    This will be refactored to read all rows for a company into a single data model.
    """
    companies = db.execute(
        "SELECT company_name, report_url, report_year FROM csr_reporting.company_csr_reports"
    )
    logger.debug(f"Companies Preview: {companies[:5]}")
    if not companies:
        logger.error("No companies found in the database. Exiting.")
        exit()

    companies_list = []
    for company_data in companies:
        company = Company(
            security=company_data["company_name"],
            esg_reports=[
                ESGReport(
                    url=company_data["report_url"], year=company_data["report_year"]
                )
            ],
        )
        companies_list.append(company)

    return companies_list


def retrieve_and_store_pdf(records: List[dict]) -> None:
    """
    Downloads all known CSR PDFs from 'csr_reporting.company_csr_reports' for a given symbol,
    and stores them in MinIO under {symbol}/{report_year}/pdf_name.
    """
    # Initialize the MinIO filesystem wrapper
    minio_fs = MinioFileSystem()

    # 3. Iterate over each record and download/store the PDF
    for row in records:
        company_name = row["company_name"]
        report_url = row["report_url"]
        report_year = str(row["report_year"])

        # Derive a filename from the URL or fallback
        file_name = report_url.split("/")[-1] or "report.pdf"

        logger.info(f"Attempting to download PDF from: {report_url}")
        try:
            # Stream-download to in-memory buffer
            response = requests.get(report_url, stream=True, timeout=15)
            if response.status_code != 200:
                logger.warning(
                    f"Failed to download {report_url} [status={response.status_code}]"
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

        # Upload to MinIO
        logger.info(
            f"Uploading '{file_name}' for {company_name}, year={report_year} to MinIO..."
        )
        try:
            object_name = minio_fs.write_pdf_bytes(
                pdf_bytes=pdf_data,
                company_id=company_name,
                report_year=report_year,
                file_name=file_name,
            )
            logger.info(f"Successfully uploaded to MinIO path: {object_name}")
        except Exception as e:
            logger.error(f"Error uploading to MinIO: {e}")


def main() -> None:
    """
    Example usage:
    1. You can loop over multiple symbols, or parse CLI arguments
    2. For demonstration, let's just do one example symbol
    """
    with PostgreSQLDB() as db:
        logger.info("Starting the retrieve_store_pdf pipeline...")
        # Get all report URLs from the database
        records = get_all_report_urls(db)
        # Iterate over each record and download/store the PDF
        retrieve_and_store_pdf(records)

    logger.info("Pipeline completed.")


if __name__ == "__main__":
    main()
