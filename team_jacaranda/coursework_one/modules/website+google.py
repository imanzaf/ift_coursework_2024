import json
import logging
import os
import sqlite3
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


# Custom cache implementation
class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


# Set base URL
BASE_URL = "https://www.responsibilityreports.com"


# Create a session with retry strategy
def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session


session = create_session()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google search configuration
GOOGLE_API_KEY = "AIzaSyA3VVtTUL8ZsXCyu_es-_V4fHLHtx1cSvE"
GOOGLE_CSE_ID = "55adbcac3c4f44f3a"

# Result save path
RESULTS_FILE = "company_pdf_links.json"


def create_google_service():
    """Create Google search service"""
    service = build(
        "customsearch",
        "v1",
        developerKey=GOOGLE_API_KEY,
        cache=MemoryCache()
    )
    return service


def read_companies_from_db(db_path):
    """Get list of companies from the database"""
    conn = None
    try:
        db_path = Path(db_path)
        if not db_path.exists():
            logger.error(f"Database file does not exist: {db_path.resolve()}")
            return []
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='equity_static'
        """)
        if not cursor.fetchone():
            logger.error("equity_static table does not exist")
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
    """Format company name, optionally replace 'company' with 'corporation'"""
    clean_name = company_name.lower()
    
    # Handle 'corp' cases first
    clean_name = clean_name.replace("corp.", "corporation")  # Handle cases with a dot
    clean_name = clean_name.replace("corp ", "corporation ")  # Handle cases with a space
    clean_name = clean_name.replace("corp-", "corporation-")  # Handle cases with a hyphen
    
    # If 'corporation' replacement is enabled
    if use_corporation:
        clean_name = clean_name.replace("company", "corporation")
    
    # Finally, handle spaces and dots
    clean_name = clean_name.replace(" ", "-")
    clean_name = clean_name.replace(".", "")
    
    return clean_name


def try_website_search(company_name, use_corporation=False):
    """Try to search for PDF links on the website"""
    formatted_name = format_company_name(company_name, use_corporation)
    search_url = f"{BASE_URL}/Company/{formatted_name}"
    logger.info(f"Attempting to access URL: {search_url}")

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
                f"Found {len(pdf_links_set)} PDF links on the website using {'corporation' if use_corporation else 'company'}")
            return list(pdf_links_set)
        return None

    except Exception as e:
        logger.error(f"Website search failed ({'corporation' if use_corporation else 'company'}): {str(e)}")
        return None


def is_valid_pdf_link(link, title=""):
    """Check if the PDF link is valid (does not contain 'annual/Annual')"""
    link_lower = link.lower()
    title_lower = title.lower()
    
    # Check if the URL or title contains "annual"
    if "annual" in link_lower or "annual" in title_lower:
        logger.info(f"Skipping annual report: {link}")
        return False
    return True


def google_search_pdf(company_name):
    """Use Google API to search for PDF files, filtering out annual reports"""
    pdf_links_set = set()

    try:
        service = create_google_service()

        # Only search recent years to save quota
        for year in range(2013, 2024):
            query = f"{company_name} {year} responsibility report sustainability report filetype:pdf"
            logger.info(f"Executing Google search: {query}")

            try:
                result = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=10).execute()

                if "items" in result:
                    for item in result["items"]:
                        link = item["link"].strip().rstrip('/')
                        title = item.get("title", "")  # Get the title of the search result
                        
                        if link.lower().endswith('.pdf') and is_valid_pdf_link(link, title):
                            pdf_links_set.add(link)
                            # Only get one valid PDF link per year
                            break

                time.sleep(1)  # Avoid triggering API limits

            except Exception as e:
                logger.error(f"Google search for year {year} failed: {str(e)}")
                # If quota is exceeded, stop searching immediately
                if "Quota exceeded" in str(e):
                    logger.error("Google API quota exceeded, stopping search")
                    break

    except Exception as e:
        logger.error(f"Failed to create Google search service: {str(e)}")

    return list(pdf_links_set)


def get_pdf_links_for_company(company_name):
    """Get all PDF links for a company using multiple search strategies"""
    logger.info(f"Starting to process company: {company_name}")

    # Strategy 1: Search on the website using the original company name
    pdf_links = try_website_search(company_name, use_corporation=False)
    if pdf_links:
        return pdf_links

    # Strategy 2: Search on the website after replacing 'company' with 'corporation'
    if "company" in company_name.lower():
        logger.info("Attempting to replace 'company' with 'corporation' and search")
        pdf_links = try_website_search(company_name, use_corporation=True)
        if pdf_links:
            return pdf_links

    # Strategy 3: Use Google API search
    logger.info("No results found on the website, attempting Google API search")
    pdf_links = google_search_pdf(company_name)

    return pdf_links


def save_results_to_json(results):
    """Save results to a JSON file"""
    try:
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        logger.info(f"Results saved to {RESULTS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save JSON: {str(e)}")


def load_existing_results():
    """Load existing results file"""
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load existing results: {str(e)}")
    return {}


def main():
    # Set database path
    # Get the absolute path of the script file
    script_dir = Path(__file__).resolve().parent
    # Build the path to the data file
    db_path = script_dir / "../../../000.Database/SQL/Equity.db"
    # Resolve the path (remove redundant ../)
    db_path = db_path.resolve()

    # Read the list of companies
    companies = read_companies_from_db(db_path)
    if not companies:
        logger.error("Failed to retrieve the list of companies")
        return

    logger.info(f"Retrieved {len(companies)} companies")

    # Load existing results
    results = load_existing_results()

    # Process each company
    for i, company in enumerate(companies, 1):
        logger.info(f"[{i}/{len(companies)}] Processing: {company}")

        # If the company has already been processed, skip
        if company in results:
            logger.info(f"{company} has already been processed, skipping")
            continue

        # Get PDF links
        pdf_links = get_pdf_links_for_company(company)

        # Save results
        results[company] = pdf_links

        # Save results after processing each company
        if i % 1 == 0:
            save_results_to_json(results)

        # Avoid making requests too frequently
        time.sleep(1)

    # Final save of results
    save_results_to_json(results)
    logger.info("All companies processed")


if __name__ == "__main__":
    main()
