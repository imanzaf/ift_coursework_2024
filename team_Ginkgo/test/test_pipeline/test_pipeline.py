import pytest
import psycopg2
import random
import sys
import os
import subprocess

# Dynamically add the path to the source files
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../modules")))

from config import DB_CONFIG
from scraper import google_search_pdf
from minio_client import download_pdf, upload_to_minio, update_minio_path

def test_scraper_to_database():
    """Test if the scraper correctly finds and stores URLs in the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Select a random company with no report_url
    cursor.execute("""
        SELECT symbol, company_name FROM Ginkgo.csr_reports 
        WHERE report_url IS NULL 
        ORDER BY RANDOM() 
        LIMIT 1;
    """)
    company = cursor.fetchone()
    
    if not company:
        pytest.skip("⚠️ Skipping: No companies found without report_url.")

    symbol, company_name = company
    year = random.randint(2014, 2024)  # Randomly select a year

    # Try scraping
    url = google_search_pdf(company_name, year)
    if url is None:
        pytest.skip(f"⚠️ Scraper did not find a URL for {company_name} ({year})")

    # Update the database
    cursor.execute("""
        UPDATE Ginkgo.csr_reports 
        SET report_url = %s 
        WHERE symbol = %s AND report_year = %s;
    """, (url, symbol, year))
    conn.commit()

    # Verify update
    cursor.execute("""
        SELECT report_url FROM Ginkgo.csr_reports 
        WHERE symbol = %s AND report_year = %s;
    """, (symbol, year))
    result = cursor.fetchone()
    
    assert result is not None and result[0] == url, "❌ Database update failed!"

    cursor.close()
    conn.close()
    print(f"✅ Scraper found & updated {company_name} ({year}) in database.")

def test_minio_storage():
    """Test if the MinIO storage system correctly handles PDF uploads."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Select a random report that has a URL but no MinIO path
    cursor.execute("""
        SELECT symbol, report_year, report_url FROM Ginkgo.csr_reports 
        WHERE report_url IS NOT NULL AND minio_path IS NULL 
        ORDER BY RANDOM() 
        LIMIT 1;
    """)
    report = cursor.fetchone()

    if not report:
        pytest.skip("⚠️ Skipping: No reports found with missing MinIO path.")

    symbol, year, report_url = report
    year = random.randint(2014, 2024)  # Randomly select a year
    pdf_filename = f"{symbol}_{year}.pdf"

    # Download PDF
    success = download_pdf(report_url, pdf_filename)
    if not success:
        pytest.skip(f"⚠️ Failed to download PDF for {symbol} ({year}), skipping upload.")

    # Upload to MinIO
    minio_url = upload_to_minio(pdf_filename, "csreport", pdf_filename)
    assert minio_url is not None, "❌ MinIO upload failed!"

    # Update database
    update_minio_path(symbol, year, minio_url)

    # Verify update
    cursor.execute("""
        SELECT minio_path FROM Ginkgo.csr_reports 
        WHERE symbol = %s AND report_year = %s;
    """, (symbol, year))
    result = cursor.fetchone()
    
    assert result is not None and result[0] == minio_url, "❌ Database MinIO path update failed!"

    # Cleanup
    os.remove(pdf_filename)

    cursor.close()
    conn.close()
    print(f"✅ PDF for {symbol} ({year}) uploaded to MinIO & database updated.")

if __name__ == "__main__":
    test_scraper_to_database()
    test_minio_storage()