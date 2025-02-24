import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os


def fetch_reports(query):
    """Retrieve reports for the specified search term (company or ticker)."""
    base_url = 'https://www.responsibilityreports.com'

    # Initiate search for the company
    search_url = f'{base_url}/Companies'
    payload = {'search': query}
    response = requests.post(search_url, data=payload)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract company link from search results
    company_link = soup.select_one('.companyName a')
    if not company_link:
        return {"error": f'Company "{query}" not found.'}

    # Navigate to the company's page
    company_url = urljoin(base_url, company_link['href'])
    response = requests.post(company_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract company name
    heading = soup.select_one('.vendor_name .heading')
    if not heading:
        return {"error": f"Could not retrieve company heading for \"{query}\"."}

    reports = {}

    # Fetch the most recent PDF report
    recent_title_elem = soup.select_one('.most_recent_content_block .bold_txt')
    recent_link_elem = soup.select_one('.most_recent_content_block .view_btn a')
    if recent_title_elem and recent_link_elem:
        recent_title = recent_title_elem.get_text(strip=True)
        recent_href = recent_link_elem.get('href')
        if recent_href:
            recent_url = urljoin(base_url, recent_href)
            recent_year = re.search(r'\d{4}', recent_title)  # Try to extract year from title
            if recent_year:
                reports[recent_year.group()] = recent_url

    # Fetch archived PDF reports
    archived_list_items = soup.select('.archived_report_content_block ul li')
    for item in archived_list_items:
        title_elem = item.select_one('.heading')
        download_link = item.select_one('.btn_archived.download a')
        if title_elem and download_link:
            archived_title = title_elem.get_text(strip=True)
            archived_href = download_link.get('href')
            if archived_href and archived_href.lower().endswith('.pdf'):
                archived_url = urljoin(base_url, archived_href)
                archived_year = re.search(r'\d{4}', archived_title)  # Try to extract year from title
                if archived_year:
                    reports[archived_year.group()] = archived_url

    if not reports:
        return {"error": f'No PDF reports found for company "{query}".'}

    # Ensure reports are sorted by year
    sorted_reports = {year: reports[year] for year in sorted(reports.keys())}

    return sorted_reports


def store_reports_for_company(name, ticker):
    """Store reports by first attempting full name search, then fallback search, and finally by ticker."""
    os.makedirs("report_links", exist_ok=True)

    # Clean company name to prepare for search
    cleaned_name = name.split('&', 1)[0].split('-', 1)[0].strip()
    cleaned_name = re.sub(r"(?<![A-Za-z])\.|\.(?![A-Za-z])|[^\w\s.]", "", cleaned_name).strip()

    # First try by the exact company name
    report_data = fetch_reports(cleaned_name)

    # If no result, try a cleaner version of the name
    if "error" in report_data:
        fallback_query = re.sub(
            r"(?i)\b(?:PLC|CO|AG|INC|LTD|CORP|CORPORATION|INCORPORATED|LLC|GMBH|SA|LIMITED|HOLDINGS|GROUP|THE|COMPANY)\b",
            "",
            name
        ).strip()
        fallback_query = fallback_query.split('&', 1)[0].split('-', 1)[0].strip()
        fallback_query = re.sub(r"(?<![A-Za-z])\.|\.(?![A-Za-z])|[^\w\s.]", "", fallback_query).strip()

        if fallback_query and fallback_query.lower() != cleaned_name.lower():
            print(f"  No reports found for '{cleaned_name}'. Trying fallback with '{fallback_query}'.")
            fallback_reports = fetch_reports(fallback_query)
            if "error" in fallback_reports:
                print(f"  Fallback search failed for {name}: {fallback_reports['error']}")
            else:
                report_data = fallback_reports
        else:
            print(f"  Error for {name}: {report_data['error']}")

    # If still no result and ticker is available, attempt search by ticker symbol
    if "error" in report_data and ticker:
        print(f"  No reports found by name. Trying ticker '{ticker}'.")
        ticker_reports = fetch_reports(ticker)
        if "error" in ticker_reports:
            print(f"  Ticker search failed for {name}: {ticker_reports['error']}")
        else:
            report_data = ticker_reports

    return report_data

def populate_reports_sustainability_reports_org(collection):
    """Populate all documents with available CSR reports using BeautifulSoup before processing."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Loop through each document and populate with available reports
    for document in collection.find():
        company_name = document["security"]
        ticker = document.get("symbol", "")  # Ensure ticker is present if needed
        logger.info(f"Populating CSR reports for company: {company_name}")

        try:
            existing_reports = document.get("csr_reports", {})

            # Fetch CSR reports using BeautifulSoup
            csr_reports = store_reports_for_company(company_name, ticker)

            if "error" in csr_reports:
                logger.warning(f"No CSR reports found for {company_name}.")
                continue

            # Append the CSR reports to the database if they are available
            update_data = {}
            for year, report_url in csr_reports.items():
                if str(year) not in existing_reports or not existing_reports[str(year)]:
                    update_data.setdefault("csr_reports", {})[str(year)] = report_url

            # Only update if new reports are found
            if update_data.get("csr_reports"):
                update_data["updated_at"] = datetime.utcnow()  # Add timestamp for update
                collection.update_one({"_id": document["_id"]}, {"$set": update_data})
                logger.info(f"Updated CSR report URLs for {company_name}")
            else:
                logger.info(f"No new CSR reports to add for {company_name}.")

        except Exception as e:
            logger.error(f"Error populating CSR reports for {company_name}: {e}")
    print("Completed processing all documents.")


if __name__ == '__main__':
    companies_to_process = [
        ("The Coca-Cola Company", "KO"),
        ("Accenture plc", "ACN"),
        ("Activision Blizzard, Inc.", "ATVI"),
        # Add more companies as needed
    ]

    for company_name, ticker in companies_to_process:
        print(f"\nProcessing company: {company_name}")
        dic = store_reports_for_company(company_name, ticker)
        print(dic)
