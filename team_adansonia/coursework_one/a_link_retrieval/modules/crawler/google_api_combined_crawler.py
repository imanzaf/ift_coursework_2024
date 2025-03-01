
import os
import re
import time
import itertools
import requests
import fitz  # PyMuPDF for PDF parsing
from dotenv import load_dotenv
from loguru import logger
from typing import List
import team_adansonia.coursework_one.a_link_retrieval.modules.validation.validation as validation
# Load environment variables
load_dotenv()

SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
API_KEYS = [
    os.getenv(f"GOOGLE_API_KEY_{i}") for i in range(1, 14)
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
    If parsing-based scoring fails, it falls back to keyword-based prioritization.
    """
    search_query = f"{company_name} {year} ESG report filetype:pdf"
    url = "https://www.googleapis.com/customsearch/v1"

    for _ in range(len(API_KEYS)):
        api_key = get_current_api_key()
        params = {"q": search_query, "key": api_key, "cx": SEARCH_ENGINE_ID}

        try:
            logger.info(f"Using API Key: {api_key}")
            response = requests.get(url, params=params, timeout=180)

            # Handle rate limits
            if response.status_code == 429:
                logger.warning(f"API Key {api_key} hit rate limit (429). Switching to next key...")
                time.sleep(2)
                continue

            # Handle forbidden (403) errors
            elif response.status_code == 403:
                logger.warning(f"API Key {api_key} is forbidden (403). Switching to next key...")
                time.sleep(2)
                continue

            response.raise_for_status()
            search_results = response.json().get("items", [])[:5]

            if not search_results:
                logger.warning(f"No ESG reports found for {company_name} ({ticker}) in {year}")
                return None

            scored_reports = []
            for result in search_results:
                title = result.get("title", "")
                description = result.get("snippet", "")
                pdf_url = result.get("link")
                cd = result.get("pagemap", {}).get("metatags", [{}])[0].get('creationdate', "")
                if pdf_url:
                    score = _score_esg_report(pdf_url, company_name, year)
                    if score is not None:
                        scored_reports.append((score, pdf_url, title, description, cd))

            if scored_reports:
                best_result = max(scored_reports, key=lambda x: x[0])
                best_url, best_title, best_desc, best_cd = best_result[1], best_result[2], best_result[3], best_result[4]
                if validation.validate_esg_report(best_url, best_title, best_desc, best_cd, company_name, year):
                    logger.info(f"✅ Best ESG report found with keywords: {best_url}")
                    return best_url

            sorted_results = _sort_search_results(company_name, ticker, year, search_results)

            if sorted_results:
                best_result = sorted_results[0]
                best_url = best_result.get("link")
                best_title = best_result.get("title", "")
                best_desc = best_result.get("snippet", "")
                best_cd = best_result.get("pagemap", {}).get("metatags", [{}])[0].get('creationdate', "")

                # Validate fallback result
                if validation.validate_esg_report(best_url, best_title, best_desc, best_cd, company_name, year):
                    logger.info(f"✅ Best ESG report found with keywords: {best_url}")
                    return best_url
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error with API Key {api_key}: {e}")
            time.sleep(2)
            continue

    logger.error("All API keys exhausted or failed. Please check API limits.")
    #throw error
    raise Exception("All API keys exhausted or failed. Please check API limits.")


def _score_search(result, company_name: str, target_year: str) -> int:
    """
    Combine all the search result scoring logic, including text, company name, and year.
    """
    stripped_name = company_name.split(" ")[0].lower()

    text_score = (
        score_text(result.get("title", "").lower())
        + score_text(result.get("snippet", "").lower())
        + (
            -10
            if (
                stripped_name not in result.get("title", "").lower()
                and stripped_name not in result.get("snippet", "").lower()
                and stripped_name not in result.get("link", "").lower()
            )
            else 5
        )
    )
    if stripped_name in result.get("link", "").lower():
        text_score += 5

    year_score = score_year(
        result.get("title", "").lower() + result.get("snippet", "").lower() + result.get("link", "").lower(),
        target_year
    )

    if "sec/" in result.get("link", "").lower() or "sec-filings/" in result.get("link", "").lower():
        text_score -= 10
    if "10-k" in result.get("title", "").lower() or "8-k" in result.get("link", "").lower():
        text_score -= 5
    if "sustainability reports archive" in result.get("link", "").lower():
        text_score += 2

    return text_score + year_score


def score_text(text: str) -> int:
    """
    Scores a text for ESG-related keywords.
    """
    keywords = ["esg", "sustainability", "report", "environmental", "social", "governance"]
    return sum(keyword in text for keyword in keywords)


def score_year(text: str, target_year: str) -> int:
    """
    Scores based on the presence of the target year in the text.
    """
    years_in_text = [int(year) for year in re.findall(r"\b\d{4}\b", text)]
    penalty = sum(-3 for year in years_in_text if year != int(target_year))
    return (5 if int(target_year) in years_in_text else -5) + penalty


def _score_esg_report(pdf_url: str, company_name: str, target_year: str) -> int:
    """
    Scores an ESG report based on ESG content, company name, and year presence.
    This function's logic remains unchanged.
    """
    try:
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()

        pdf_document = fitz.open(stream=response.content, filetype="pdf")
        text = "".join(pdf_document[page_num].get_text("text").lower() for page_num in range(min(3, len(pdf_document))))
        pdf_document.close()

        score = 0
        esg_keywords = ["esg", "sustainability", "environmental", "social", "governance"]

        if any(keyword in text for keyword in esg_keywords):
            score += 10

        stripped_name = company_name.split()[0].lower()
        if stripped_name in text:
            score += 10
        else:
            logger.warning(f"❌ Company name '{stripped_name}' not found in document.")
            return None

        year_count = text.count(target_year) + text.count(str(int(target_year) - 1))
        if year_count > 1:
            score += 5
        else:
            logger.warning(f"❌ Input year '{target_year}' not found in document.")
            return None

        sec_terms = ["10-k", "8-k", "securities and exchange commission"]
        if any(term in text for term in sec_terms):
            score -= 15

        logger.info(f"✅ ESG report {pdf_url} scored: {score}")
        return score
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch PDF: {e}")
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
    return None


def _sort_search_results(company_name: str, ticker: str, year: str, search_results: List[dict]) -> List[dict]:
    """
    Sort search results based on relevance to the company, ticker, and year.
    """
    for result in search_results:
        result["score"] = _keyword_based_score(company_name, ticker, year, result)
    return sorted(search_results, key=lambda item: item.get("score", 0), reverse=True)


def _keyword_based_score(company_name: str, ticker: str, year: str, result: dict) -> int:
    """ Score results based on keywords if PDF parsing fails """
    stripped_name = company_name.split(" ")[0].lower()
    score = sum(keyword in result.get("title", "").lower() + result.get("snippet", "").lower() for keyword in
                ["esg", "sustainability", "report"])
    if stripped_name in result.get("title", "").lower() or stripped_name in result.get("snippet", "").lower():
        score += 5
    if year in result.get("title", "") or year in result.get("snippet", ""):
        score += 5
    return score


if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    ticker = input("Enter the company ticker (or leave blank): ")
    year = input("Enter the year for the ESG report: ")

    esg_url = _get_report_search_results(company_name, ticker, year)
    if esg_url:
        print(f"✅ Highest scoring ESG report URL: {esg_url}")
    else:
        print("❌ No valid ESG report found.")
