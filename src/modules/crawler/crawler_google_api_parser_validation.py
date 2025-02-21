import os
import requests
import time
import itertools
import fitz  # PyMuPDF for PDF parsing
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
API_KEYS = [
    os.getenv("GOOGLE_API_KEY_1"),
    os.getenv("GOOGLE_API_KEY_2"),
    os.getenv("GOOGLE_API_KEY_3"),
    os.getenv("GOOGLE_API_KEY_4"),
    os.getenv("GOOGLE_API_KEY_5"),
    os.getenv("GOOGLE_API_KEY_6"),
    os.getenv("GOOGLE_API_KEY_7"),
    os.getenv("GOOGLE_API_KEY_8"),
    os.getenv("GOOGLE_API_KEY_9"),
    os.getenv("GOOGLE_API_KEY_10"),
    os.getenv("GOOGLE_API_KEY_11"),
    os.getenv("GOOGLE_API_KEY_12"),
    os.getenv("GOOGLE_API_KEY_13"),
]

if not all(API_KEYS) or not SEARCH_ENGINE_ID:
    raise ValueError("Missing API keys or SEARCH_ENGINE_ID in environment variables.")

api_key_cycle = itertools.cycle(API_KEYS)

def get_current_api_key():
    """Get the next API key from the cycle"""
    return next(api_key_cycle)

def _get_report_search_results(company_name: str, ticker: str, year: str) -> str:
    """
    Retrieve and score ESG report URLs, returning the best-scoring valid report.
    """
    search_query = f"{company_name} {year} ESG report filetype:pdf"
    url = "https://www.googleapis.com/customsearch/v1"

    for _ in range(len(API_KEYS)):
        api_key = get_current_api_key()
        params = {
            "q": search_query,
            "key": api_key,
            "cx": SEARCH_ENGINE_ID,
        }

        try:
            logger.info(f"Using API Key: {api_key}")
            response = requests.get(url, params=params)

            if response.status_code == 429:
                logger.warning(f"API Key {api_key} hit rate limit (429). Switching to next key...")
                time.sleep(2)
                continue

            response.raise_for_status()
            search_results = response.json().get("items", [])[:5]

            if not search_results:
                logger.warning(f"No ESG reports found for {company_name} ({ticker}) in {year}")
                return None

            # Score all reports and return the best one
            scored_reports = []
            for result in search_results:
                pdf_url = result.get("link")
                if pdf_url:
                    score = _score_esg_report(pdf_url, company_name, year)
                    if score is not None:
                        scored_reports.append((score, pdf_url))

            if scored_reports:
                best_report = max(scored_reports, key=lambda x: x[0])
                logger.info(f"✅ Best ESG report found: {best_report[1]} (Score: {best_report[0]})")
                return best_report[1]

            # After processing all 5 results, if no valid report is found, return None
            logger.warning(f"No valid ESG reports found after checking 5 links.")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error with API Key {api_key}: {e}")
            time.sleep(2)
            continue

    logger.error("All API keys exhausted or failed. Please check API limits.")
    return None

def _score_esg_report(pdf_url: str, company_name: str, target_year: str) -> int:
    """
    Scores an ESG report based on:
    ✅ ESG content presence
    ✅ Company name presence
    ✅ Input year presence (higher mentions = higher score)
    ❌ Penalties for SEC reports (10-K, 8-K, SEC document)
    """
    try:
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()

        # Open the PDF file in memory
        pdf_document = fitz.open(stream=response.content, filetype="pdf")

        # Extract text from the first few pages
        text = ""
        for page_num in range(min(3, len(pdf_document))):  # Check up to first 3 pages
            text += pdf_document[page_num].get_text("text").lower()

        pdf_document.close()

        # Score Calculation
        score = 0

        # Keywords for ESG content validation
        esg_keywords = [
            "esg", "csr", "environmental", "social", "governance", "sustainability",
            "carbon footprint", "climate change", "greenhouse gases",
            "corporate responsibility", "esg report", "net zero"
        ]

        # Ensure the document contains ESG-related terms
        if any(keyword in text for keyword in esg_keywords):
            score += 10  # ESG content found

        # Ensure company name is in the document
        stripped_name = company_name.split()[0].lower()  # First word of company name
        if stripped_name in text:
            score += 10  # Company name present
        else:
            logger.warning(f"❌ Company name '{stripped_name}' not found in document.")
            return None  # Reject this document

        # Ensure the input year is in the document
        year_count = text.count(target_year) + text.count(str(int(target_year) - 1))
        if year_count > 1:
            score += 5  # Base + 2 points per mention
            logger.info(f"✅ Year '{target_year}' found")
        else:
            logger.warning(f"❌ Input year '{target_year}' not found in document.")
            return None  # Reject this document

        # Penalties for SEC-related documents
        sec_terms = ["10-k", "8-k", "united states securities and exchange commission"]
        if any(term in text for term in sec_terms):
            score -= 15  # Penalize heavily
            logger.warning(f"❌ SEC-related terms found. Score reduced by 15.")

        logger.info(f"✅ ESG report {pdf_url} scored: {score}")
        return score

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch PDF: {e}")
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")

    logger.warning("❌ ESG-related content not found in document.")
    return None

# Example usage
if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    ticker = input("Enter the company ticker (or leave blank): ")
    year = input("Enter the year for the ESG report: ")

    esg_url = _get_report_search_results(company_name, ticker, year)
    if esg_url:
        print(f"✅ Highest scoring ESG report URL: {esg_url}")
    else:
        print("❌ No valid ESG report found.")
