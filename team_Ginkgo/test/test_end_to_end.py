import pytest
import psycopg2
import random
import os
import sys
import subprocess

# Dynamically add the path to the source files
# Get the absolute path of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up two levels to ift_coursework_2024, then enter modules
modules_path = os.path.abspath(os.path.join(current_dir, "../modules"))
# Add modules/csr_scraper to Python's module search path
sys.path.append(modules_path)

# Now we can correctly import config, scraper, and minio_client
from config import DB_CONFIG
from scraper import google_search_pdf
from minio_client import download_pdf, upload_to_minio, update_minio_path

def test_end_to_end():
    """Full end-to-end test: Scrape → Store → Download → Upload to MinIO → Update DB"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 1️⃣ Select a random company from the database that needs a CSR report
    cursor.execute("""
        SELECT symbol, company_name FROM Ginkgo.csr_reports 
        WHERE report_url IS NULL 
        ORDER BY RANDOM() 
        LIMIT 1;
    """)
    company = cursor.fetchone()

    if not company:
        pytest.skip("⚠️ No available companies without report_url in the database.")

    symbol, company_name = company
    year = random.randint(2014, 2024)  # Randomly select a year

    # 2️⃣ Scrape the report URL
    url = google_search_pdf(company_name, year)
    if url is None:
        pytest.skip(f"⚠️ Scraper did not find a report for {company_name} ({year}).")

    # 3️⃣ Update the database with the scraped URL
    cursor.execute("""
        UPDATE Ginkgo.csr_reports 
        SET report_url = %s 
        WHERE symbol = %s AND report_year = %s;
    """, (url, symbol, year))
    conn.commit()

    # 4️⃣ Download the PDF
    pdf_filename = f"{symbol}_{year}.pdf"
    success = download_pdf(url, pdf_filename)
    if not success:
        pytest.skip(f"⚠️ Failed to download PDF for {company_name} ({year}), skipping MinIO upload.")

    # 5️⃣ Upload the PDF to MinIO
    minio_url = upload_to_minio(pdf_filename, "csreport", pdf_filename)
    assert minio_url is not None, "❌ MinIO upload failed."

    # 6️⃣ Update the database with MinIO storage path
    update_minio_path(symbol, year, minio_url)

    # 7️⃣ Verify that MinIO path is correctly stored in the database
    cursor.execute("""
        SELECT minio_path FROM Ginkgo.csr_reports 
        WHERE symbol = %s AND report_year = %s;
    """, (symbol, year))
    result = cursor.fetchone()
    
    assert result is not None and result[0] == minio_url, "❌ Database MinIO path update failed."

    # 8️⃣ Cleanup test PDF file
    os.remove(pdf_filename)

    cursor.close()
    conn.close()

    print(f"✅ End-to-end test PASSED for {company_name} ({year}).")

def test_code_quality():
    """Run linting, formatting, and security scans for the entire module."""
    python_exec = sys.executable  # Get the correct Python path

    print("🔍 Running flake8 on the entire module...")
    subprocess.run([python_exec, "-m", "flake8", "../../modules", "--max-line-length=100"], check=True)

    print("🔍 Checking code formatting with black...")
    subprocess.run([python_exec, "-m", "black", "--check", "../../modules"], check=True)

    print("🔍 Sorting imports with isort...")
    subprocess.run([python_exec, "-m", "isort", "--check-only", "../../modules"], check=True)

    print("🔍 Running security scans with Bandit...")
    subprocess.run([python_exec, "-m", "bandit", "-r", "../../modules"], check=True)

if __name__ == "__main__":
    test_end_to_end()
    test_code_quality()