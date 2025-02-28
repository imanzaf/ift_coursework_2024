import os
import requests
import hashlib
import re
import json
import time
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import sqlite3
import logging
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
import tempfile
from googleapiclient.http import set_user_agent

# Custom Cache Implementation
class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


# Setting the base URL
BASE_URL = "https://www.responsibilityreports.com"


# Creating a Session with a Retry Policy
def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session


session = create_session()

# Configuration log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google Search
GOOGLE_API_KEY = "AIzaSyA3VVtTUL8ZsXCyu_es-_V4fHLHtx1cSvE"
GOOGLE_CSE_ID = "55adbcac3c4f44f3a"

# Result Save Path
script_dir = Path(__file__).resolve().parent
RESULTS_FILE = script_dir / "../../../team_jacaranda/coursework_one/modules/db/company_pdf_links.json"
# Resolve the path (remove redundant ../)
RESULTS_FILE = RESULTS_FILE.resolve()

def create_google_service():
    """Creating Google Search Service"""
    service = build(
        "customsearch",
        "v1",
        developerKey=GOOGLE_API_KEY,
        cache=MemoryCache()
    )
    return service


def read_companies_from_db(db_path):
    """Get List from Database"""
    conn = None
    try:
        db_path = Path(db_path)
        if not db_path.exists():
            logger.error(f"Database file does not exist：{db_path.resolve()}")
            return []
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='equity_static'
        """)
        if not cursor.fetchone():
            logger.error("equity_static doesn't exist")
            return []
        cursor.execute("SELECT security FROM equity_static")
        companies = [row[0] for row in cursor.fetchall()]
        logger.info(f"Successfully read {len(companies)} companies from the database")
        return companies
    except Exception as e:
        logger.error(f"Database read error: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()


def format_company_name(company_name, use_corporation=False):
    """Format the company name, optionally replacing company with corporation"""
    clean_name = company_name.lower()
    
    # corp
    clean_name = clean_name.replace("corp.", "corporation")
    clean_name = clean_name.replace("corp ", "corporation ")
    clean_name = clean_name.replace("corp-", "corporation-")
    
    # corporation subsititution
    if use_corporation:
        clean_name = clean_name.replace("company", "corporation")
    
    clean_name = clean_name.replace(" ", "-")
    clean_name = clean_name.replace(".", "")
    
    return clean_name


def try_website_search(company_name, use_corporation=False):
    """Try searching the website for PDF links"""
    formatted_name = format_company_name(company_name, use_corporation)
    search_url = f"{BASE_URL}/Company/{formatted_name}"
    logger.info(f"Try to access the URL: {search_url}")

    try:
        response = session.get(search_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links_set = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.lower().endswith('.pdf'):
                full_url = BASE_URL + href if not href.startswith('http') else href
                full_url = full_url.strip().rstrip('/')
                pdf_links_set.add(full_url)

        if pdf_links_set:
            logger.info(
                f"Useing{'corporation' if use_corporation else 'company'}finds from website {len(pdf_links_set)} 个PDF链接")
            return list(pdf_links_set)
        return None

    except Exception as e:
        logger.error(f"Website Search Failure ({'corporation' if use_corporation else 'company'}): {str(e)}")
        return None


def is_valid_pdf_link(link, title=""):
    """Check if the PDF link works（excluding annual/Annual）"""
    link_lower = link.lower()
    title_lower = title.lower()
    
    if "annual" in link_lower or "annual" in title_lower:
        logger.info(f"Skip annual report: {link}")
        return False
    return True


def google_search_pdf(company_name):
    """Use Google API to search PDF files, filter out annual reports"""
    pdf_links_set = set()

    try:
        service = create_google_service()

        for year in range(2013, 2024):
            query = f"{company_name} {year} responsibility report sustainability report filetype:pdf"
            logger.info(f"Perform a Google search: {query}")

            try:
                result = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=10).execute()

                if "items" in result:
                    for item in result["items"]:
                        link = item["link"].strip().rstrip('/')
                        title = item.get("title", "")  # Get the title of the search result
                        
                        if link.lower().endswith('.pdf') and is_valid_pdf_link(link, title):
                            pdf_links_set.add(link)
                            # Get only one valid PDF link per year
                            break

                time.sleep(1)  # Avoid triggering API restrictions

            except Exception as e:
                logger.error(f"Year {year} Google Search fails: {str(e)}")
                # Stop searching immediately if you encounter a quota limit
                if "Quota exceeded" in str(e):
                    logger.error("Google API quota has been exceeded, stop searching")
                    break

    except Exception as e:
        logger.error(f"Google Search Service Creation Failure: {str(e)}")

    return list(pdf_links_set)


def get_pdf_links_for_company(company_name):
    """Get access to all of the company's PDF links, using a variety of search strategies"""
    logger.info(f"Commencement of processing of companies: {company_name}")

    # Tactic 1: Use the original company name to search the site
    pdf_links = try_website_search(company_name, use_corporation=False)
    if pdf_links:
        return pdf_links

    # Tactic 2: Replace company with corporation and search the site.
    if "company" in company_name.lower():
        logger.info("Try searching after replacing 'company' with 'corporation'")
        pdf_links = try_website_search(company_name, use_corporation=True)
        if pdf_links:
            return pdf_links

    # Tactic 3: Search using Google API
    logger.info("Site search did not find results, try using the Google API search")
    pdf_links = google_search_pdf(company_name)

    return pdf_links


def save_results_to_json(results):
    """Save the result as a JSON file"""
    try:
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        logger.info(f"The results have been saved to {RESULTS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save JSON: {str(e)}")


def load_existing_results():
    """Loading an existing results file"""
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load existing result: {str(e)}")
    return {}


def main():
    # Setting the database path
    db_path = r"./000.Database/SQL/Equity.db"

    # 首先修改数据库
    logger.info("开始修改数据库...")
    modify_database(db_path)



    # Reading company list
    companies = read_companies_from_db(db_path)
    if not companies:
        logger.error("Failed to get list")
        return

    logger.info(f"Get {len(companies)} companies in total")

    # Loading current results
    results = load_existing_results()

    # Handling every results
    for i, company in enumerate(companies, 1):
        logger.info(f"[{i}/{len(companies)}] Handling: {company}")

        # Skip if company has already dealt with it
        if company in results:
            logger.info(f"{company} have been handled,skip.")
            continue

        # get pdf links
        pdf_links = get_pdf_links_for_company(company)

        # save results
        results[company] = pdf_links

        # Save results once per company processed
        if i % 1 == 0:
            save_results_to_json(results)

        # Avoid requests that are too frequent
        time.sleep(1)

    # Final saved results
    save_results_to_json(results)
    logger.info("All company processing completed")


if __name__ == "__main__":
    main()
