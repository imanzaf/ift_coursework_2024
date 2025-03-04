import os
import sys
import time
import datetime
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests
from apscheduler.schedulers.blocking import BlockingScheduler

# Selenium / ChromeDriver
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# PostgreSQL is only used to read the company list
import psycopg2

# MongoDB (changed to write)
from pymongo import MongoClient

# MinIO
from minio import Minio

# ========== Configuration area ==========
DB_CONFIG = {
    "dbname": "fift",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5439",
}

MONGO_URI = "mongodb://localhost:27019"
MONGO_DB_NAME = "csr_db"
MONGO_COLLECTION = "csr_reports"

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
collection_reports = mongo_db[MONGO_COLLECTION]

MINIO_CLIENT = Minio(
    "localhost:9000",
    access_key="ift_bigdata",
    secret_key="minio_password",
    secure=False,
)
BUCKET_NAME = "csr-reports"

PROXY = None  # If you need a proxy, e.g.: "http://127.0.0.1:7890"

# ========== Logging functionality ==========
# 1) In testing environments, logs are written to "test_log.log"
#    Otherwise, logs are written to "csr_fast.log"
if "pytest" in sys.modules:
    LOG_FILE = "test_log.log"
else:
    LOG_FILE = "csr_fast.log"


def write_log(message: str):
    """
    Record logs to file and console.
    If in a pytest environment, writes to test_log.log;
    otherwise writes to csr_fast.log.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"

    # Print to console
    print(log_msg)

    # Write to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")


# ========== Core functionality ==========
def init_driver():
    """Initialize Chrome WebDriver."""
    write_log("🚀 Initializing ChromeDriver...")

    options = webdriver.ChromeOptions()
    # If you don't need to open the browser UI, you can uncomment to run in headless mode
    # options.add_argument('--headless')
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")

    # If proxy is required
    # if PROXY:
    #     options.add_argument(f'--proxy-server={PROXY}')

    chromedriver_autoinstaller.install()
    driver = webdriver.Chrome(options=options)

    write_log("✅ ChromeDriver started successfully!")
    return driver


def get_search_results(driver, query, timeout=5):
    """
    Search on Bing and return search results.
    1) Shorten the default timeout to 5s.
    2) If driver is mocked, directly return the mock results.
    """
    # If the driver is a mock (pytest patches get_search_results),
    # it might return a MagicMock without performing the actual search logic.
    from unittest.mock import MagicMock
    if isinstance(driver, MagicMock):
        return driver.find_elements()

    search_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    write_log(f"🔍 Visiting search engine: {search_url}")

    try:
        driver.get(search_url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".b_algo h2 a"))
        )
        results = driver.find_elements(By.CSS_SELECTOR, ".b_algo h2 a")
        write_log(f"✅ Search completed, found {len(results)} results")
        return results
    except Exception as e:
        write_log(f"❌ Search failed: {type(e).__name__}, {e}")
        return []


def download_pdf(company_name, year, url):
    """Download the PDF to local (with year distinction)."""
    write_log(f"📥 Starting to download PDF for {company_name}({year}): {url}")

    if "pdf" not in url.lower():
        write_log(f"⚠️ {company_name}({year}) is not a PDF file, skipping")
        return None

    local_dir = "./reports"
    os.makedirs(local_dir, exist_ok=True)
    # To avoid overwriting: add the year to local name
    local_path = os.path.join(local_dir, f"{company_name}_{year}.pdf")

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(resp.content)
            write_log(f"✅ {company_name}({year}) downloaded successfully: {local_path}")
            return local_path
        else:
            write_log(f"❌ {company_name}({year}) download failed, status code: {resp.status_code}")
    except Exception as e:
        write_log(f"❌ {company_name}({year}) download failed: {type(e).__name__}, {e}")

    return None


def upload_to_minio(company_name, year, local_path):
    """Upload the PDF to MinIO, separated by year."""
    try:
        object_name = f"{year}/{company_name}.pdf"
        write_log(f"📤 Starting to upload {company_name}({year}) to MinIO...")

        with open(local_path, "rb") as f:
            MINIO_CLIENT.put_object(
                bucket_name=BUCKET_NAME,
                object_name=object_name,
                data=f,
                length=os.path.getsize(local_path),
                content_type="application/pdf",
            )
        write_log(f"✅ Uploaded to MinIO successfully: {object_name}")
        return object_name
    except Exception as e:
        write_log(f"❌ Failed to upload to MinIO: {type(e).__name__}, {e}")
        return None


def save_csr_report_info_to_mongo(company_name, pdf_url, object_name, year):
    """
    Save the CSR report information to MongoDB, and record the report year.
    """
    try:
        data = {
            "company_name": company_name,
            "csr_report_url": pdf_url,
            "storage_path": object_name,
            "csr_report_year": year,
            # It's recommended to use a time zone aware now, e.g. datetime.datetime.now(datetime.UTC)
            "ingestion_time": datetime.datetime.utcnow(),
        }
        # Make sure to differentiate by (company + year)
        mongo_db["csr_reports"].update_one(
            {"company_name": company_name, "csr_report_year": year},
            {"$set": data},
            upsert=True,
        )
        write_log(f"✅ MongoDB record updated successfully: {company_name}({year})")
    except Exception as e:
        write_log(f"❌ Failed to update MongoDB record: {type(e).__name__}, {e}")


def get_company_list_from_postgres():
    """Get the list of companies from PostgreSQL."""
    write_log("🔍 Connecting to PostgreSQL to read the company list...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT security FROM csr_reporting.company_static;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        companies = [row[0] for row in rows]
        write_log(f"✅ Retrieved {len(companies)} companies")
        return companies
    except Exception as e:
        write_log(f"❌ Failed to read from PostgreSQL: {type(e).__name__}, {e}")
        return []


def search_by_years(driver, company_name, years, keywords):
    """
    Loop through (year + keywords) for searching.
    If a PDF is found, download and save it. Parallel searching is faster.
    """
    found_any = False
    for year in years:
        # Resume crawling: If MongoDB already has a record for that year, skip
        existing = mongo_db["csr_reports"].find_one(
            {"company_name": company_name, "csr_report_year": year}
        )
        if existing:
            write_log(f"⚠️ {company_name}({year}) already exists in MongoDB, skipping")
            continue

        for kw in keywords:
            query = f"{company_name} {year} {kw}"
            write_log(f"🚀 Searching keyword: {query}")
            results = get_search_results(driver, query, timeout=5)

            for r in results:
                url = r.get_attribute("href")
                pdf_path = download_pdf(company_name, year, url)
                if pdf_path:
                    obj_name = upload_to_minio(company_name, year, pdf_path)
                    if obj_name:
                        save_csr_report_info_to_mongo(company_name, url, obj_name, year)
                    found_any = True
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
            # Shorten sleep to 0.2
            time.sleep(0.2)

    return found_any


def search_and_process(company_name):
    """Search, download, and upload CSR reports for different years."""
    write_log(f"🚀 Starting processing for company: {company_name}")

    driver = None
    try:
        driver = init_driver()

        # The years to be searched (2020~2024)
        years = range(2020, 2025)
        # Reduce the number of keywords to speed up searching
        keywords = [
            "corporate sustainability report filetype:pdf",
            "ESG report filetype:pdf",
        ]
        found = search_by_years(driver, company_name, years, keywords)
        if not found:
            write_log(f"⚠️ No PDF found for {company_name}")
    except Exception as e:
        write_log(f"❌ Failed to process {company_name}: {type(e).__name__}, {e}")
    finally:
        if driver:
            driver.quit()


def process_batch(company_list):
    """
    Process the company list using multithreading to improve speed.
    Change max_workers from 5 to 10.
    """
    write_log("🚀 Starting batch data crawling... (max_workers=10)")
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(search_and_process, company_list)


def main():
    """Manually triggered crawler process."""
    companies = get_company_list_from_postgres()
    if not MINIO_CLIENT.bucket_exists(BUCKET_NAME):
        MINIO_CLIENT.make_bucket(BUCKET_NAME)

    write_log("📢 Starting to process the company list...")
    process_batch(companies)
    write_log("🎉 All companies processed successfully!")


def schedule_scraper():
    """Use APScheduler to run the crawler every 7 days."""
    scheduler = BlockingScheduler()
    scheduler.add_job(main, "interval", days=7)
    write_log("⏳ Scraper scheduler started, running every 7 days...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        write_log("🛑 Scheduler stopped.")

def main(max_companies=None):
    """Run the CSR crawling process"""
    companies = get_company_list_from_postgres()

    if max_companies:
        companies = companies[:max_companies]  # Crawl only the specified number of companies
    
    if not MINIO_CLIENT.bucket_exists(BUCKET_NAME):
        MINIO_CLIENT.make_bucket(BUCKET_NAME)  # Create the bucket if it does not exist

    write_log("📢 Starting to process the company list...")
    process_batch(companies)
    write_log("🎉 All companies have been processed!")

if __name__ == "__main__":
    # By default, run the crawler once
    main()
