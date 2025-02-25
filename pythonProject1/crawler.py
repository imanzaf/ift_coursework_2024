import datetime
import hashlib
import logging
import os
import random
import threading
import time
import urllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set

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


class Config:
    REPORTS_DIR = "./reports"
    LOGS_DIR = "./logs"
    MAX_WORKERS = 5
    REQUEST_TIMEOUT = 60
    PDF_MIN_LENGTH = 1000
    VALID_KEYWORDS = {'sustainability', 'esg', 'csr', 'environment', 'social'}
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ]
    SEARCH_YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
    MAX_PAGES_PER_YEAR = 2
    CSV_PATH = "C:/Users/赵小蕊/Desktop/ift_coursework_2024_Wisteria/nasdaq.csv"
    RETRY_DELAY = (1, 5)
    MAX_RETRIES = 3
    BROWSER_TIMEOUT = 600
    MAX_LINKS_PER_YEAR = 3

# MinIO setting
    MINIO_ENDPOINT = "localhost:9000"   
    MINIO_ACCESS_KEY = "ift_bigdata"   
    MINIO_SECRET_KEY = "minio_password" 
    MINIO_BUCKET = "csreport"  

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(Config.LOGS_DIR, 'crawler.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFScraper:
    def __init__(self):
        self.driver_pool = []
        self.lock = threading.Lock()
        self.seen_urls: Set[str] = set()
        self.seen_hashes: Set[str] = set()
        self._init_directories()
        requests.packages.urllib3.disable_warnings()
        self.current_user_agent = random.choice(Config.USER_AGENTS)
        self.minio_client = Minio(
            "localhost:9000",
            access_key="ift_bigdata",
            secret_key="minio_password",
            secure=False)
        from reports.database import PostgresManager
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
        options.add_argument(f'user-agent={self.current_user_agent}')
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


    def search_pdfs(self, company: str) -> Dict[int, List[str]]:
        """Search for PDF links across multiple years"""
        year_results = {}
        driver = self.get_driver()

        try:
            for year in Config.SEARCH_YEARS:
                search_query = f"{company} csr report {year} filetype:pdf"
                search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}"

                try:
                    driver.get(search_url)
                    WebDriverWait(driver, Config.BROWSER_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.b_algo')))

                    collected_links = []
                    for _ in range(Config.MAX_PAGES_PER_YEAR):
                        results = driver.find_elements(By.CSS_SELECTOR, '.b_algo h2 a')
                    page_links = [
                        result.get_attribute('href')
                        for result in results
                        if result.get_attribute('href') and
                           result.get_attribute('href').lower().endswith('.pdf')
                    ]
                    collected_links.extend(page_links)

                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, 'a.sb_pagN')
                        driver.execute_script("arguments[0].click();", next_btn)
                        WebDriverWait(driver, Config.BROWSER_TIMEOUT).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.b_algo')))
                        time.sleep(random.uniform(*Config.RETRY_DELAY))
                    except (NoSuchElementException, TimeoutException):
                        break

                    # Filter and deduplicate links
                    valid_links = [
                                      link for link in collected_links
                                      if any(kw in link.lower() for kw in ['csr','esg','sustainability','responsibility','environment'])
                                         and str(year) in link
                                  ][:Config.MAX_LINKS_PER_YEAR]

                    year_results[year] = list(set(valid_links))

                except WebDriverException as e:
                    logger.error(f"Year {year} search failed: {str(e)}")

        finally:
            self.return_driver(driver)
        return year_results

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

                    if self.file_exists_in_minio(filename):
                        logger.info(f"Skipping {filename}, already in MinIO.")
                        return False


                
                    with self.lock:
                        if content_hash in self.seen_hashes:
                            logger.info(f"Skipped duplicate content: {url}")
                            return False
                        self.seen_hashes.add(content_hash)

                    # Year-specific filename
                    filename = f"{company}_{year}.pdf"
                     #  MinIO
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
                    # 插入数据库
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

    def validate_pdf(self, path: str) -> bool:
        """Validate PDF content"""
        try:
            with pdfplumber.open(path) as pdf:
                text = "\n".join(page.extract_text() or '' for page in pdf.pages)
                return len(text) >= Config.PDF_MIN_LENGTH and \
                    any(kw in text.lower() for kw in Config.VALID_KEYWORDS)
        except Exception as e:
            logger.error(f"PDF validation failed: {str(e)}")
            return False

    def process_company(self, company: str) -> Dict:
        """Process multiple years for a single company"""
        result = {
            'company': company,
            'downloaded': [],
            'failed_years': []
        }

        try:
            year_links = self.search_pdfs(company)
            if not year_links:
                return result

            for year, urls in year_links.items():
                if not urls:
                    result['failed_years'].append(year)
                    continue

                success = False
                for url in urls:
                    if url in self.seen_urls:
                        continue

                    if self.download_pdf(company, url, year):
                        result['downloaded'].append({'year': year, 'url': url})
                        self.seen_urls.add(url)
                        success = True
                        break  # Stop after first successful download per year

                if not success:
                    result['failed_years'].append(year)

            return result

        except Exception as e:
            logger.error(f"Company processing failed: {company} - {str(e)}")
            return result

    def run(self):
        """Main execution flow"""
        logger.info("Starting multi-year scraping process...")

        try:
            df = pd.read_csv(Config.CSV_PATH)
            companies = df["Name"].dropna().unique().tolist()
            logger.info(f"Loaded {len(companies)} companies")

            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                futures = {executor.submit(self.process_company, co): co for co in companies[1:4]}

                for future in as_completed(futures):
                    company = futures[future]
                    try:
                        result = future.result(timeout=Config.BROWSER_TIMEOUT)
                        logger.info(f"Processed {company}: {len(result['downloaded'])} PDFs")
                    except TimeoutError:
                        logger.error(f"Timeout processing {company}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing {company}: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
        finally:
            self.cleanup_drivers()
            logger.info("Scraping completed!")

    def cleanup_drivers(self):
        """Cleanup browser instances"""
        with self.lock:
            while self.driver_pool:
                driver = self.driver_pool.pop()
                try:
                    driver.quit()
                except Exception as e:
                    logger.error(f"Driver cleanup error: {str(e)}")


if __name__ == "__main__":
    scraper = PDFScraper()
    scraper.run()