"""
retrieve_store_pdf/main.py

Retrieves each row from csr_reporting.company_csr_reports and downloads/stores
the PDF in MinIO. Bypasses local storage by streaming to memory.
"""

import os
import sys
import io
import requests
from typing import List
from loguru import logger

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.database.postgres import PostgreSQLDB
from src.database.minio_utils import MinioFileSystem


def fetch_csr_reports(symbol: str) -> List[dict]:
    """
    Query all rows from csr_reporting.company_csr_reports for a single symbol.
    Returns list of dicts: {symbol, report_url, report_year, ...}
    """
    with PostgreSQLDB() as db:
        results = db.get_csr_reports_by_symbol(symbol)
        logger.info(f"[{symbol}] Found {len(results)} rows in company_csr_reports.")
    return results


def retrieve_and_store_pdf(symbol: str):
    """
    Downloads all known CSR PDFs from 'csr_reporting.company_csr_reports' for a given symbol,
    and stores them in MinIO under {symbol}/{report_year}/pdf_name.
    """
    records = fetch_csr_reports(symbol)
    if not records:
        logger.warning(f"No CSR report URLs found for symbol={symbol}. Skipping.")
        return

    minio_fs = MinioFileSystem()

    for row in records:
        report_url = row["report_url"]
        report_year = str(row["report_year"])
        file_name = report_url.split("/")[-1] or "report.pdf"

        logger.info(f"Attempting to download PDF from: {report_url}")
        try:
            response = requests.get(report_url, stream=True, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Failed to download {report_url} [status={response.status_code}]")
                continue

            pdf_buffer = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_buffer.write(chunk)

            pdf_buffer.seek(0)
            pdf_data = pdf_buffer.read()

        except Exception as e:
            logger.error(f"Error downloading {report_url}: {e}")
            continue

        # Upload to MinIO
        logger.info(f"Uploading '{file_name}' for symbol={symbol}, year={report_year} to MinIO...")
        try:
            object_name = minio_fs.write_pdf_bytes(
                pdf_bytes=pdf_data,
                company_id=symbol,
                report_year=report_year,
                file_name=file_name
            )
            logger.info(f"Successfully uploaded to MinIO path: {object_name}")
        except Exception as e:
            logger.error(f"Error uploading to MinIO: {e}")


def main():
    """
    Example usage:
    1. You can loop over multiple symbols, or parse CLI arguments
    2. For demonstration, let's just do one example symbol
    """
    logger.info("Starting the retrieve_store_pdf pipeline...")

    example_symbol = "AAPL"
    retrieve_and_store_pdf(example_symbol)

    # Or do multiple:
    # for sym in ["AAPL", "MSFT", "TSLA"]:
    #     retrieve_and_store_pdf(sym)

    logger.info("retrieve_store_pdf pipeline completed.")


if __name__ == "__main__":
    main()
