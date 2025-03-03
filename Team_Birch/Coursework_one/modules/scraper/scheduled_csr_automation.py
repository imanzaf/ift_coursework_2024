
import os
import time
import datetime
import urllib.parse
import threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, wait

import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from googlesearch import search
import pdfplumber

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
import subprocess


# =================== Database & MinIO Configuration ===================
DB_CONFIG = {
    "dbname": "your_db",
    "user": "your_user",
    "password": "your_password",
    "host": "localhost",  # adjust if remote
    "port": "5432",       # adjust if needed
}

MINIO_CLIENT = Minio(
    "localhost:9000",     # adjust if remote
    access_key="your_minio_access_key",
    secret_key="your_minio_secret_key",
    secure=False          # set to True if using HTTPS
)
BUCKET_NAME = "csr-reports"


# =================== Utility Functions ===================
def connect_postgres():
    """
    Connect to PostgreSQL database.
    """
    return psycopg2.connect(**DB_CONFIG)


def fetch_companies_from_db():
    """
    Retrieve a list of companies from PostgreSQL.
    Adjust the SQL query or add WHERE conditions if you only want certain companies.
    """
    query = "SELECT security FROM csr_reporting.company_static;"
    try:
        conn = connect_postgres()
        cur = conn.cursor()
        cur.execute(query)
        companies = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return companies
    except Exception as e:
        print(f"Failed to retrieve companies: {e}")
        return []


def save_report_to_postgres(company_name, pdf_url, object_name, year):

    query = """
    INSERT INTO csr_reporting.csr_reports (company_name, csr_report_url, storage_path, csr_report_year)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (company_name, csr_report_year) DO NOTHING;
    """
    try:
        conn = connect_postgres()
        cur = conn.cursor()
        cur.execute(query, (company_name, pdf_url, object_name, year))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to store report info in PostgreSQL: {e}")


def upload_to_minio(company_name, year, local_path):
    """
    Upload a local PDF to MinIO, returning the object name if successful.
    """
    object_name = f"{year}/{company_name}.pdf"
    try:
        with open(local_path, "rb") as f:
            MINIO_CLIENT.put_object(
                bucket_name=BUCKET_NAME,
                object_name=object_name,
                data=f,
                length=os.path.getsize(local_path),
                content_type="application/pdf",
            )
        print(f"Uploaded to MinIO as {object_name}")
        return object_name
    except Exception as e:
        print(f"MinIO upload failed: {e}")
        return None


def download_and_check_pdf(company_name, year, pdf_url):
    """
    Download the PDF from the given URL and check for the keywords 'Scope 1' or 'Scope 2'.
    Return the local file path if it contains those keywords; otherwise, None.
    """
    pdf_dir = "./reports"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{company_name}_{year}.pdf")

    try:
        # Download
        response = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30, verify=False)
        if response.status_code == 200:
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded PDF: {pdf_path}")

            # Check contents
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                if "Scope 1" in text or "Scope 2" in text:
                    return pdf_path
                else:
                    # Remove if not containing keywords
                    os.remove(pdf_path)
                    print(f"PDF does not contain 'Scope 1' or 'Scope 2': {pdf_path}")
        else:
            print(f"Failed to download PDF from {pdf_url}, status code: {response.status_code}")
    except Exception as e:
        print(f"PDF download error: {e}")

    return None


def process_company(company_name):



    year = datetime.datetime.now().year

    # Disable SSL warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Global variables
    LOG_FILENAME = None
    STATS = None

    # Initialize Selenium WebDriver
    def init_driver():
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--log-level=3')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("user-agent=Mozilla/5.0")
        return webdriver.Chrome(service=webdriver.ChromeService(ChromeDriverManager().install()), options=options)

    # Write logs
    def write_log(message):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    # Extract text from a PDF file
    def extract_text_from_pdf(pdf_path):
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {pdf_path} - {e}")
        return text

    # Search for PDF links in Bing
    def search_pdf_in_bing(driver, company_name):
        search_query = f"{company_name} sustainability report 2024 filetype:pdf"
        search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}"

        write_log(f"Searching Bing: {company_name} | URL: {search_url}")
        driver.get(search_url)

        try:
            results = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.b_algo h2 a'))
            )
            pdf_links = [r.get_attribute('href') for r in results if r.get_attribute('href').endswith(".pdf")]
            return pdf_links[0] if pdf_links else None
        except:
            return None

    # Search for PDF links in Google
    def search_pdf_in_google(company_name):
        try:
            query = f"{company_name} sustainability report 2024 filetype:pdf"
            results = search(query, num=5, stop=5, pause=2)
            return next((url for url in results if url.endswith(".pdf")), None)
        except:
            return None

    # Search company sustainability webpage if no direct PDF is found
    def search_webpage_in_bing(driver, company_name):
        search_query = f"{company_name} sustainability report"
        search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}"

        write_log(f"Searching Webpage in Bing: {company_name} | URL: {search_url}")
        driver.get(search_url)

        try:
            results = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.b_algo h2 a'))
            )
            return [r.get_attribute('href') for r in results if not r.get_attribute('href').endswith(".pdf")][:3]
        except:
            return None

    # Find and extract PDF from a sustainability webpage
    def find_pdf_in_webpage(driver, company_name, url):
        write_log(f"Searching for PDF in webpage: {company_name} | URL: {url}")
        driver.get(url)

        try:
            results = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
            pdf_links = [r.get_attribute('href') for r in results if
                         r.get_attribute('href') and ".pdf" in r.get_attribute('href')]
            return pdf_links[0] if pdf_links else None
        except:
            return None

    # Download and process a PDF file
    def download_pdf(company_name, url):
        if 'pdf' not in url:
            write_log(f"{company_name}: Not a PDF URL | URL: {url}")
            return None

        headers = {'User-Agent': 'Mozilla/5.0'}
        pdf_path = f"./reports/{company_name}.pdf"

        try:
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            if response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)

                text = extract_text_from_pdf(pdf_path)
                if "Scope 1" in text or "Scope 2" in text:
                    write_log(f"{company_name}: Valid PDF downloaded | URL: {url}")
                    return pdf_path
                else:
                    os.remove(pdf_path)
                    write_log(f"{company_name}: PDF does not contain Scope 1/2 | URL: {url}")
                    return None
        except:
            return None

    # Process a single company
    def process_company(company_name):
        driver = init_driver()

        pdf_url = search_pdf_in_bing(driver, company_name) or search_pdf_in_google(company_name)

        if not pdf_url:
            webpages = search_webpage_in_bing(driver, company_name)
            if webpages:
                for webpage in webpages:
                    pdf_url = find_pdf_in_webpage(driver, company_name, webpage)
                    if pdf_url:
                        break

        if pdf_url:
            download_pdf(company_name, pdf_url)
        else:
            write_log(f"{company_name}: No PDF found")

        driver.quit()

    # Process companies from CSV file
    def process_batch_from_csv(companies, batch_num):
        global STATS
        STATS = {'total_companies': 0, 'direct_pdf_success': 0, 'webpage_pdf_success': 0, 'failed_companies': []}

        global LOG_FILENAME
        LOG_FILENAME = f'./logs/crawler_batch{batch_num}_log.txt'

        batch_companies = companies[batch_num::10]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_company, company_name) for company_name in batch_companies]
            wait(futures)

    # Main execution
    if __name__ == "__main__":
        os.makedirs('./reports', exist_ok=True)
        os.makedirs('./logs', exist_ok=True)

        csv_file = "/Users/sherrie/Desktop/nasdaq.csv"
        df = pd.read_csv(csv_file, encoding="utf-8")
        company_column = df.columns[0]
        companies = df[company_column].dropna().unique().tolist()

        for batch_num in range(10):
            process_batch_from_csv(companies, batch_num)

        print("Scraping completed!")


    # e.g.: pdf_url = your_crawler(company_name, year)
    pdf_url = "https://example.com/some_report.pdf"  # placeholder

    if not pdf_url:
        print(f"No PDF URL found for {company_name}")
        return

    # Download & check PDF
    local_path = download_and_check_pdf(company_name, year, pdf_url)
    if not local_path:
        print(f"No valid PDF for {company_name}")
        return

    # Upload to MinIO
    object_name = upload_to_minio(company_name, year, local_path)
    if not object_name:
        print(f"Failed to upload PDF for {company_name}")
        # If desired, keep or remove local file on failure
        return

    # Store metadata in DB
    save_report_to_postgres(company_name, pdf_url, object_name, year)

    # Clean up local file
    os.remove(local_path)
    print(f"Finished processing {company_name}.")


def process_companies():
    """
    Batch process for all companies retrieved from the DB.
    """
    companies = fetch_companies_from_db()
    for company in companies:
        process_company(company)


# =================== Entry Point & Scheduling Placeholder ===================

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def extract_csr_data():
    """
    Initiates the process of gathering, uploading, and storing metadata
    for CSR (Corporate Social Responsibility) reports.
    """
    logging.info("Beginning CSR data extraction...")
    try:
        # Execute the Python script responsible for CSR data handling
        subprocess.run(["python", "download_upload_metadata.py"], check=True)
        logging.info("CSR data and metadata collection completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run the CSR data process: {e}")


def main():
    scheduler = BackgroundScheduler()

    # Schedule this job every Sunday at 3 AM
    scheduler.add_job(extract_csr_data, 'cron', day_of_week='sun', hour=3, minute=0)
    scheduler.start()

    logging.info("Scheduler is active. CSR data process will run every Sunday at 3 AM.")

    try:
        while True:
            time.sleep(60)  # Keep the main script running
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler has been shut down.")


if __name__ == "__main__":
    main()

