import os
import requests
import time
import yaml
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from modules.db_loader.sqlite_loader import fetch_companies
from modules.minio_writer.minio_client import upload_to_minio
from modules.url_parser.extract_year import extract_year_from_url_or_snippet
from modules.db_loader.mongo_db import get_mongo_collection

# Load environment variables from .env file
load_dotenv()

# Load configuration from YAML file, using a default path for Docker if not set in environment variables
config_path = os.getenv("CONF_PATH", "a_pipeline/config/conf.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# API keys for Google Custom Search
API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Connect to MongoDB
collection = get_mongo_collection()

# Ensure CSR Reports directory exists
os.makedirs("CSR_Reports", exist_ok=True)


def google_search_csr_reports(company_name):
    """
    Search for CSR report PDFs using Google Custom Search API.

    Args:
        company_name (str): The company name to search for.

    Returns:
        list[tuple]: List of tuples containing PDF links and snippets.
    """
    query = f"{company_name} sustainability report filetype:pdf"
    url = f"https://www.googleapis.com/customsearch/v1?q={requests.utils.quote(query)}&key={API_KEY}&cx={SEARCH_ENGINE_ID}"
    response = requests.get(url)

    if response.status_code == 200:
        results = response.json().get("items", [])
        pdf_links = [
            (item["link"], item.get("snippet", ""))
            for item in results
            if item["link"].lower().endswith(".pdf")
        ]
        return pdf_links
    print(f"Google API Error for {company_name}: {response.status_code}")
    return []


def bing_search_csr_reports(company_name):
    """
    Scrape Bing for CSR report PDFs using BeautifulSoup.

    Args:
        company_name (str): The company name to search for.

    Returns:
        list[tuple]: List of tuples containing PDF links and snippets.
    """
    query = f"{company_name} sustainability report filetype:pdf"
    search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("a", href=True)
        pdf_links = list(set(link["href"] for link in results if ".pdf" in link["href"]))
        return [(link, "") for link in pdf_links]

    print(f"Bing search failed for {company_name}: {response.status_code}")
    return []


def get_reports_json(company_name):
    """
    Scrape responsibilityreports.com for CSR report PDFs.

    Args:
        company_name (str): The company name to search for.

    Returns:
        list[tuple]: List of tuples containing PDF links and snippets.
    """
    base_url = "https://www.responsibilityreports.com"
    search_url = f"{base_url}/Companies"
    payload = {"search": company_name}
    response = requests.post(search_url, data=payload)
    soup = BeautifulSoup(response.text, "html.parser")

    company_link = soup.select_one(".companyName a")
    if not company_link:
        return []

    company_url = urljoin(base_url, company_link["href"])
    response = requests.post(company_url)
    soup = BeautifulSoup(response.text, "html.parser")

    reports = []
    most_recent_title_elem = soup.select_one(".most_recent_content_block .bold_txt")
    most_recent_link_elem = soup.select_one(".most_recent_content_block .view_btn a")
    if most_recent_title_elem and most_recent_link_elem:
        recent_report_url = urljoin(base_url, most_recent_link_elem.get("href"))
        reports.append((recent_report_url, most_recent_title_elem.get_text(strip=True)))

    archived_lis = soup.select(".archived_report_content_block ul li")
    for li in archived_lis:
        title_elem = li.select_one(".heading")
        download_link = li.select_one(".btn_archived.download a")
        if title_elem and download_link:
            archive_url = urljoin(base_url, download_link.get("href"))
            reports.append((archive_url, title_elem.get_text(strip=True)))

    return reports


def report_exists(company_name, report_year):
    """
    Check if a report for the given company and year already exists in MongoDB.

    Args:
        company_name (str): The company name.
        report_year (str): The year of the report.

    Returns:
        bool: True if the report exists, False otherwise.
    """
    return collection.find_one({"company_name": company_name, "report_year": report_year}) is not None


def fetch_and_store_reports(company):
    """
    Fetch and store CSR reports for a given company.

    Args:
        company (dict): Dictionary containing company details.
    """
    print(f"\nSearching CSR reports for: {company['company_name']}")

    pdf_links = google_search_csr_reports(company["company_name"])
    pdf_links += bing_search_csr_reports(company["company_name"])
    pdf_links += get_reports_json(company["company_name"])

    if pdf_links:
        for pdf_link, snippet in pdf_links:
            report_year = extract_year_from_url_or_snippet(pdf_link, snippet)

            if report_exists(company["company_name"], report_year):
                print(f"Skipping already stored report for {company['company_name']} ({report_year})")
                continue  # Avoid duplicate uploads

            print(f"Storing report for {report_year}: {pdf_link}")
            try:
                pdf_response = requests.get(pdf_link, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if pdf_response.status_code == 200:
                    pdf_name = pdf_link.split("/")[-1].split("?")[0]
                    local_pdf_path = os.path.join("CSR_Reports", pdf_name)

                    # Save PDF locally
                    with open(local_pdf_path, "wb") as pdf_file:
                        pdf_file.write(pdf_response.content)

                    # Upload to MinIO and get stored URL
                    minio_pdf_url = upload_to_minio(local_pdf_path, company["symbol"], pdf_name)

                    # Store report details in MongoDB
                    collection.insert_one(
                        {
                            **company,
                            "pdf_link": pdf_link,
                            "report_year": report_year,
                            "minio_url": minio_pdf_url,
                        }
                    )
                else:
                    print(f"Failed to download {pdf_link}")
            except Exception as e:
                print(f"Error downloading {pdf_link}: {e}")
    else:
        print("No CSR PDF reports found.")

    # Delay to prevent excessive requests
    time.sleep(2)


# Fetch CSR reports for each company in the database
companies = fetch_companies()
for company in companies:
    fetch_and_store_reports(company)

print("\nFinished fetching and uploading CSR reports.")
