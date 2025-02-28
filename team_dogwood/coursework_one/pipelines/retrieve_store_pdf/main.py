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
    companies = db.fetch(
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


def retrieve_and_store_pdf(records: List[Company]) -> None:
    """
    Downloads all known CSR PDFs from 'csr_reporting.company_csr_reports' for a given symbol,
    and stores them in MinIO under {symbol}/{report_year}/pdf_name.
    """
    # Initialize the MinIO filesystem wrapper
    minio_fs = MinioFileSystem()

    # 3. Iterate over each record and download/store the PDF
    for company in records:
        for report in company.esg_reports:
            # Derive a filename from the URL or fallback
            file_name = report.url.split("/")[-1] or "report.pdf"

            logger.info(f"Attempting to download PDF from: {report.url}")
            try:
                # Stream-download to in-memory buffer
                response = requests.get(report.url, stream=True, timeout=15)
                if response.status_code != 200:
                    logger.warning(
                        f"Failed to download {report.url} [status={response.status_code}]. Skipping."
                    )
                    continue

                pdf_buffer = io.BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        pdf_buffer.write(chunk)

                # Get the size of the data in BytesIO object
                pdf_buffer.seek(0, io.SEEK_END)  # Move to the end
                file_size = pdf_buffer.tell()  # Get size of data
                pdf_buffer.seek(0)  # Reset the pointer back to the start

            except Exception as e:
                logger.error(f"Error downloading {report.url}: {e}. Skipping.")
                continue

            # Upload to MinIO
            logger.info(
                f"Uploading '{file_name}' for {company.security}, year={report.year} to MinIO..."
            )
            try:
                object_name = minio_fs.write_pdf_bytes(
                    pdf_bytes=pdf_buffer,
                    company_id=company.security,
                    report_year=report.year,
                    file_name=file_name,
                    file_size=file_size,
                )
                logger.info(f"Successfully uploaded to MinIO path: {object_name}")
            except Exception as e:
                logger.error(f"Error uploading to MinIO: {e}")
                raise Exception("Failed to upload PDF to MinIO.")


def main() -> None:
    """
    Loop over all report URLs in the database and download/store the PDFs.
    """
    try:
        with PostgreSQLDB() as db:
            logger.info("Starting the retrieve_store_pdf pipeline...")
            # Get all report URLs from the database
            records = get_all_report_urls(db)
            # Iterate over each record and download/store the PDF
            retrieve_and_store_pdf(records)

        logger.info("Pipeline run successful.")
    except Exception as e:
        logger.error(f"Pipeline run failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
