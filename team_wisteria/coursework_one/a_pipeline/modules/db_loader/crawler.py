import hashlib
import logging
import os
import random
import threading
import time
import urllib.parse
import re
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Any

import sys
import schedule
import pandas as pd
import pdfplumber
import requests
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------
# Configuration
# -----------------------------
class Config:
    REPORTS_DIR = "./reports"
    LOGS_DIR = "./logs"
    MAX_WORKERS = 5
    REQUEST_TIMEOUT = 60
    PDF_MIN_LENGTH = 1000
    VALID_KEYWORDS = {'sustainability', 'esg', 'csr', 'environment', 'social', 'responsibility'}
    USER_AGENTS = [
        # ###### "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"]
    SEARCH_YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
    MAX_PAGES_PER_YEAR = 2
    CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../static/nasdaq.csv"))
    RETRY_DELAY = (1, 5)
    MAX_RETRIES = 3
    BROWSER_TIMEOUT = 600
    MAX_LINKS_PER_YEAR = 3
    COMPANY_LIST_URL = "https://www.responsibilityreports.com/Companies?searchTerm="
    NUMBER = 0
# MinIO setting
    MINIO_ENDPOINT = "localhost:9000"   
    MINIO_ACCESS_KEY = "ift_bigdata"   
    MINIO_SECRET_KEY = "minio_password" 
    MINIO_BUCKET = "csreport"  

# -----------------------------
# Initialize directories and logger
# -----------------------------
os.makedirs(Config.REPORTS_DIR, exist_ok=True)
os.makedirs(Config.LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(Config.LOGS_DIR, 'crawler.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -----------------------------
# Main Scraper Class
# -----------------------------
class PDFScraper:
    """
    Scrapes PDF reports from responsibilityreports.com.
    First, it searches using Bing for "sustainability report" PDFs.
    If no PDF is found directly, it then searches for the company's sustainability website via Bing
    and extracts PDF links from that page.
    After downloading, PDF content is validated to ensure it contains expected keywords and the company name.
    """
    def __init__(self):
        self.driver_pool = []
        self.lock = threading.Lock()
        self.seen_urls: Set[str] = set()
        self.seen_hashes: Set[str] = set()
        self._init_directories()
        requests.packages.urllib3.disable_warnings()
        self.current_user_agent = Config.USER_AGENTS[0]
        self.minio_client = Minio(
            "localhost:9000",
            access_key="ift_bigdata",
            secret_key="minio_password",
            secure=False)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", ".."))
        sys.path.append(project_root)

        from team_wisteria.coursework_one.a_pipeline.modules.url_parser.database import PostgresManager
        self.pg_manager = PostgresManager(host="localhost", port="5439")
        self.minio_client = Minio(
            Config.MINIO_ENDPOINT,
            access_key=Config.MINIO_ACCESS_KEY,
            secret_key=Config.MINIO_SECRET_KEY,
            secure=False
        )


    def _init_directories(self):
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)

    def init_driver(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument(f'--user-agent={self.current_user_agent}')
        # options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # options.add_argument('--disable-blink-features')
        # options.add_argument('--disable-blink-features=AutomationControlled')
        # options.add_argument('--window-size=1960, 1080')
        service = webdriver.ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def get_driver(self) -> webdriver.Chrome:
        with self.lock:
            return self.driver_pool.pop() if self.driver_pool else self.init_driver()

    def return_driver(self, driver: webdriver.Chrome):
        with self.lock:
            self.driver_pool.append(driver)
    def file_exists_in_db(self, file_hash: str) -> bool:
        return self.pg_manager.check_pdf_record(file_hash)

    def file_exists_in_minio(self, filename: str) -> bool:
        try:
            self.minio_client.stat_object(Config.MINIO_BUCKET, filename)
            return True
        except S3Error:
            return False
    

    # -----------------------------
    # Direct PDF search using Bing
    # -----------------------------
    def search_pdfs(self, company: str) -> Dict[int, List[str]]:
        """Search for PDF links for each year using Bing."""
        year_results = {}
        driver = self.get_driver()
        try:
            for year in Config.SEARCH_YEARS:
                query = f"{company} sustainability report {year} filetype:pdf"
                search_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
                # print("company --> " + company)
                # print("search_url --> " + str(year))
                # print(search_url)
                driver.get(search_url)
                WebDriverWait(driver, Config.BROWSER_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.b_algo'))
                )
                collected_links = []
                for _ in range(Config.MAX_PAGES_PER_YEAR):
                    results = driver.find_elements(By.CSS_SELECTOR, '.b_algo h2 a')
                    page_links = [result.get_attribute('href') for result in results
                                  if result.get_attribute('href') and result.get_attribute('href').lower().endswith('.pdf')]
                    collected_links.extend(page_links)
                    # ###### print("collected_links")
                    # ###### print(collected_links)
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, 'a.sb_pagN')
                        driver.execute_script("arguments[0].click();", next_btn)
                        WebDriverWait(driver, Config.BROWSER_TIMEOUT).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.b_algo'))
                        )
                        time.sleep(random.uniform(*Config.RETRY_DELAY))
                    except (NoSuchElementException, TimeoutException):
                        break
                valid_links = [link for link in collected_links if
                               any(kw in link.lower() for kw in ['csr','esg','sustainability','responsibility'])
                               and str(year) in link][:Config.MAX_LINKS_PER_YEAR]
                # print("valid_links")
                # print(valid_links)
                # print("====================")
                year_results[year] = list(set(valid_links))
        except WebDriverException as e:
            logger.error(f"Year search failed: {str(e)}")
        finally:
            self.return_driver(driver)
        return year_results

    # -----------------------------
    # Helper: write_log
    # -----------------------------
    def write_log(self, message: str):
        logger.info(message)

    # -----------------------------
    # Helper: get_search_results
    # -----------------------------
    def get_search_results(self, driver: webdriver.Chrome, company_name: str, url: str, locator: tuple) -> List[Any]:
        try:
            driver.get(url)
            WebDriverWait(driver, Config.BROWSER_TIMEOUT).until(
                EC.presence_of_element_located(locator)
            )
            time.sleep(2)
            return driver.find_elements(locator[0], locator[1])
        except Exception as e:
            logger.error(f"{company_name}: Error getting search results from {url}: {str(e)}")
            return []

    # -----------------------------
    # Fallback Step 2: Search company's sustainability webpage via Bing
    # -----------------------------
    def search_webpage_in_bing(self, driver: webdriver.Chrome, company_name: str, year: int) -> Any:
        query = f"{company_name} sustainability report {year} -responsibilityreports"
        search_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&first=1&form=QBRE"
        self.write_log(f"{company_name}: Searching webpage in Bing | URL: {search_url}")
        locator = (By.CSS_SELECTOR, '.b_algo h2 a')
        search_results = self.get_search_results(driver, company_name, search_url, locator)
        if not search_results:
            self.write_log(f"{company_name}: No search results found | URL: {search_url}")
            return None
        url_list = []
        count = 0
        for result in search_results:
            if count >= 3:
                break
            try:
                url = result.get_attribute('href')
                if url and '.pdf' not in url.lower():
                    url_list.append(url)
                    count += 1
            except Exception as e:
                self.write_log(f"{company_name}: Error getting URL from search result: {str(e)}")
                continue
        if not url_list:
            self.write_log(f"{company_name}: No valid URL found in search results")
            return None
        return url_list

    # -----------------------------
    # Fallback Step 3: Find PDF links on company's sustainability webpage
    # -----------------------------
    def find_pdf_in_webpage(self, driver: webdriver.Chrome, company_name: str, url: str, target_year: int) -> Any:
        self.write_log(f"{company_name}: Searching for PDF on webpage | URL: {url}")
        locator = (By.TAG_NAME, "a")
        search_results = self.get_search_results(driver, company_name, url, locator)
        if not search_results:
            self.write_log(f"{company_name}: No search results found | URL: {url}")
            return None
        pdf_links = []
        for result in search_results:
            try:
                href = result.get_attribute('href')
                if not href:
                    continue
                is_pdf = ('.pdf' in href.lower())
                text = result.text.lower()
                # Adjust filtering: accept if text or URL contains a 4-digit year or keywords
                if href and (re.search(r"20\d{2}", text) or re.search(r"20\d{2}", href) or
                             any(keyword in text for keyword in ['report', 'sustainability', 'esg', 'csr', 'annual', 'year'])):
                    pdf_links.append(href)
            except Exception as e:
                continue
        self.write_log(f"{company_name}: Found {len(pdf_links)} PDF links on webpage.")
        if not pdf_links:
            return None
        # Attempt to download the first valid PDF among the first 10 links using the target year
        for pdf in pdf_links[:10]:
            if self.download_pdf_method(company_name, pdf, target_year):
                return pdf
        self.write_log(f"{company_name}: No valid PDF found on webpage")
        return None

    # Modified wrapper: call download_pdf with a specified target_year
    def download_pdf_method(self, company: str, url: str, target_year: int) -> bool:
        return self.download_pdf(company, url, target_year)

    # -----------------------------
    # Download PDF and validate
    # -----------------------------
    def download_pdf(self, company: str, url: str, year: int) -> bool:
        filename = f"{company}_{year}.pdf"
        
        for attempt in range(Config.MAX_RETRIES + 1):
            try:
                time.sleep(random.uniform(*Config.RETRY_DELAY))
                response = requests.get(
                    url,
                    headers={'User-Agent': self.current_user_agent},
                    timeout=Config.REQUEST_TIMEOUT,
                    verify=False,
                    stream=True
                )

                if response.status_code == 200:
                    content_hash = hashlib.md5(response.content).hexdigest()

                    if self.file_exists_in_db(content_hash):
                        logger.info(f"Skipping {filename}, already in DB (file_hash={content_hash})")
                        return False

                    # if self.file_exists_in_minio(filename):
                    #     logger.info(f"Skipping {filename}, already in MinIO.")
                    #     return False


                
                    with self.lock:
                        if content_hash in self.seen_hashes:
                            logger.info(f"Skipped duplicate content: {url}")
                            return False
                        self.seen_hashes.add(content_hash)

                    # Year-specific filename
                    filename = f"{company}_{year}.pdf"
                    #  #  MinIO
                    try:
                        self.minio_client.put_object(
                            Config.MINIO_BUCKET,
                            filename,
                            data=BytesIO(response.content),
                            length=len(response.content),
                            content_type="application/pdf"
                        )
                    except S3Error as e:
                        logger.error(f"MinIO upload failed: {str(e)}")
                        return False
                    # Insertion into the database
                    record = {
                    "company": company,
                    "url": url,
                    "year": year,
                    "file_hash": content_hash,
                    "created_at": datetime.datetime.now().isoformat(),
                    "filename": filename
                    }
                    # Postgres
                    self.pg_manager.insert_pdf_record(record)
                    logger.info(f"[Download] {company}-{year} success. Saved to DBs.")


                elif response.status_code >= 500:
                    logger.warning(f"Server error ({response.status_code}), retrying...")
                    time.sleep(2 ** attempt)

            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {str(e)}")

        return False

    # -----------------------------
    # Validate PDF content with extra check for company name
    # -----------------------------
    def validate_pdf(self, path: str, company: str = None) -> bool:
        try:
            with pdfplumber.open(path) as pdf:
                text = "\n".join(page.extract_text() or '' for page in pdf.pages)
                if len(text) < Config.PDF_MIN_LENGTH:
                    return False
                text_lower = text.lower()
                if not any(kw in text_lower for kw in Config.VALID_KEYWORDS):
                    return False
                # Extra check: if company name is provided, ensure it appears in the content
                company1 = company.split()
                company2 = " ".join(company1[:1])  # use first words to verify whether
                # company name can be found in PDF content
                if company2 and company2.lower() not in text_lower:
                    # print("++++++")
                    # print(path)
                    # print(company)
                    # print("++++++")
                    logger.info(f"Company name '{company}' not found in PDF content.")
                    return False
                return True
        except Exception as e:
            logger.error(f"PDF validation failed: {str(e)}")
            return False

    # -----------------------------
    # Process a single company
    # -----------------------------
    def process_company(self, company: str) -> Dict:
        result = {
            'company': company,
            'downloaded': [],
            'failed_years': []
        }
        try:
            # First, attempt direct Bing search for PDFs
            year_links = self.search_pdfs(company)
            # print(year_links)
            # print("year_links")
            # time.sleep(2000)
            for year in Config.SEARCH_YEARS:
                # os.makedirs(Config.REPORTS_DIR + "/" + company + "/" + str(year), exist_ok=True)
                downloaded = False
                candidate_urls = year_links.get(year, [])
                # print("++++----")
                # print(candidate_urls)
                # time.sleep(2000)
                if candidate_urls:
                    for url in candidate_urls:
                        if url in self.seen_urls:
                            continue
                        if self.download_pdf(company, url, year):
                            result['downloaded'].append({'year': year, 'url': url})
                            self.seen_urls.add(url)
                            downloaded = True
                            break  # Only one PDF per year is needed
                # If direct Bing search fails for this year, use fallback search
                if not downloaded:
                    driver = self.get_driver()
                    bing_urls = self.search_webpage_in_bing(driver, company, year)
                    fallback_found = False
                    if bing_urls:
                        for fallback_url in bing_urls:
                            # In fallback, pass the current target year
                            pdf_path = self.find_pdf_in_webpage(driver, company, fallback_url, year)
                            if pdf_path:
                                if self.download_pdf(company, pdf_path, year):
                                    result['downloaded'].append({'year': year, 'url': pdf_path})
                                    fallback_found = True
                                    break
                    if not downloaded and not fallback_found:
                        result['failed_years'].append(year)
            return result
        except Exception as e:
            logger.error(f"Company processing failed: {company} - {str(e)}")
            return result

    # -----------------------------
    # Main execution flow
    # -----------------------------
    def run(self):
        logger.info("Starting multi-year scraping process...")
        try:
            df = pd.read_csv(Config.CSV_PATH)
            companies = df["Name"].dropna().unique().tolist()
            logger.info(f"Loaded {len(companies)} companies")
            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                futures = {executor.submit(self.process_company, co): co for co in companies}
                for future in as_completed(futures):
                    company = futures[future]
                    try:
                        result = future.result(timeout=Config.BROWSER_TIMEOUT)
                        logger.info(f"Processed {company}: {len(result['downloaded'])} PDFs downloaded")
                    except TimeoutError:
                        logger.error(f"Timeout processing {company}")
                    except Exception as e:
                        logger.error(f"Error processing {company}: {str(e)}")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
        finally:
            self.cleanup_drivers()
            logger.info("Scraping completed!")

    def cleanup_drivers(self):
        with self.lock:
            while self.driver_pool:
                driver = self.driver_pool.pop()
                try:
                    driver.quit()
                except Exception as e:
                    logger.error(f"Driver cleanup error: {str(e)}")


# User can choose to scrape immediately or every week, every month or every quarter
def run_schedule():
    scraper = PDFScraper()

    # clear tasks
    schedule.clear()
    # run every 3 seconds
    print("Please select time interval you want to run scraper,")
    print("Please input 1, 2, 3, 4:")
    print("1. run immediately")
    print("2. run every week")
    print("3. run every month")
    print("4. run every quarter")
    choice = input()
    print(choice)

    if choice == "1":
        scraper.run()
    elif choice == "2":
        print("You choose to scrape every week, please wait...")
        schedule.every().week.do(scraper.run)
    elif choice == "3":
        print("You choose to scrape every month, please wait...")
        schedule.every(30).days.do(scraper.run)
    elif choice == "4":
        print("You choose to scrape every quarter, please wait...")
        schedule.every(90).days.do(scraper.run)
    else:
        print("Incorrect input.")

    while True:
        schedule.run_pending()


if __name__ == "__main__":
    run_schedule()
