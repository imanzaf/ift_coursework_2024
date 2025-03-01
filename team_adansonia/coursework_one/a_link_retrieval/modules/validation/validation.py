import re
from datetime import datetime, time
import fitz
from Crypto.SelfTest.Hash.test_cSHAKE import descr
#from jsonref import requests
import requests
import fitz  # PyMuPDF
import urllib3
# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def validate_esg_report(url: str, title: str, desc: str, cd: str, company_name: str, year: int) -> bool:
    """
    Validate whether a URL is a proper ESG report for a given company and year.

    :param url: The URL of the potential ESG report.
    :param metadata: The metadata or parsed data from the URL (e.g., title, description).
    :param company: The company's name.
    :param year: The expected report year.
    :return: True if valid, False otherwise.
    """
    stripped_name = company_name.split(" ")[0].lower()
    normalized_content = (url + " " + title + " " + desc).lower()  # Combine URL and metadata for validation
    ESG_KEYWORDS = {"sustainability", "environmental", "social responsibility", "governance", "csr", "esg",
                    "climate change", "carbon footprint", "renewable energy", "greenhouse gas emissions", "biodiversity",
                    "deforestation", "pollution", "waste management", "water conservation", "recycling", "sustainable development",
                    "corporate social responsibility", "labor practices",
                     "impact", "social responsibility","environmental impact", "social impact", "governance practices", "esg reporting",
                    "sustainable", "net zero", "carbon neutrality", "climate action", "greenwashing",
                    "environmental justice", "social equity", "corporate governance", "ethical investing", "sustainable agriculture",
                    "clean technology", "green building", "environmental policy", "social innovation", "corporate ethics"}

    # Ensure the content contains at least one ESG-related keyword
    if not any(keyword in normalized_content for keyword in ESG_KEYWORDS):
        return False
    # Ensure the content contains at least one ESG-related keyword
    SEC_KEYWORDS = {
        "sec/", "sec-filings/"
    }
    if any(keyword in url.lower() for keyword in SEC_KEYWORDS):
        return False
    # Ensure the normalized company name appears in the content
    if stripped_name not in normalized_content:
        return False

    # Ensure the given year appears in the content
    if str(year) not in normalized_content:
        return False

    match = re.search(r"D:(\d{4})", cd)
    if match:
        extracted_year = match.group(1)
        if extracted_year != str(year):
            return False  # Reject if creation year doesn't match input year
    else:
        return False

    return True



def is_valid_esg_report_from_url(pdf_url: str, company_name: str, year: str) -> bool:
    """
    Fetches a PDF from a URL, extracts text from the first 35 pages,
    and checks if it meets ESG criteria.

    :param pdf_url: URL of the PDF.
    :param company_name: The company name.
    :param year: The expected report year.
    :return: True if it meets ESG criteria, False otherwise.
    """
    ESG_KEYWORDS = {
        "sustainability", "environmental", "social responsibility", "governance", "csr", "esg",
        "climate change", "carbon footprint", "renewable energy", "greenhouse gas emissions",
        "biodiversity", "deforestation", "pollution", "waste management", "water conservation",
        "recycling", "sustainable development", "corporate social responsibility", "labor practices",
        "impact", "social responsibility", "environmental impact", "social impact", "governance practices",
        "sustainable", "net zero", "carbon neutrality", "climate action", "greenwashing",
        "environmental justice", "social equity", "corporate governance", "ethical investing",
        "sustainable agriculture", "clean technology", "green building", "environmental policy",
        "social innovation", "corporate ethics"
    }

    SEC_KEYWORDS = {
        "securities and exchange commission"
    }

    stripped_name = company_name.lower().split()[0]

    try:
        # Fetch the PDF into memory
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(pdf_url, headers=headers, verify=False, timeout=30)

        # Check if the request was successful
        if response.status_code != 200 or "pdf" not in response.headers.get("Content-Type", ""):
            print(f"Failed to fetch PDF: {pdf_url}")
            return False

        # Open PDF from memory stream
        pdf_document = fitz.open(stream=response.content, filetype="pdf")

        # Extract text from the first 2 pages (or fewer if the document is shorter)
        num_pages = min(2, len(pdf_document))
        text = "".join(pdf_document[page].get_text("text").lower() for page in range(num_pages))

        pdf_document.close()

        # Check for ESG keywords
        if not any(keyword in text.lower() for keyword in ESG_KEYWORDS):
            return False
        if any(keyword in text.lower() for keyword in SEC_KEYWORDS):
            return False
        # Check if the company name appears
        if stripped_name not in text:
            return False

        # Check if the given year appears
        if str(year) not in text:
            return False

        return True  # The PDF meets the ESG criteria

    except Exception as e:
        print(f"Error processing PDF: {pdf_url}, Error: {str(e)}")
        return False
