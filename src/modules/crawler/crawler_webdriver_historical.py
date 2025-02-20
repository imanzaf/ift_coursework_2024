import os
import sys
import time
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def _get_report_search_results(company_name: str, ticker: str, year: str) -> str:
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    search_query = f"{company_name} {year} ESG report filetype:pdf"
    search_url = f"https://www.google.com/search?q={search_query}"
    driver.get(search_url)

    time.sleep(2)  # Allow page to load
    search_results = driver.find_elements(By.CSS_SELECTOR, 'a')
    esg_urls = []

    for result in search_results:
        url = result.get_attribute('href')
        if url and url.endswith(".pdf") and year in url:
            esg_urls.append(url)

    driver.quit()

    if not esg_urls:
        logger.warning(f"No ESG reports found for {company_name} or ticker {ticker} in {year}")
        sys.exit()

    sorted_results = _sort_search_results(company_name, ticker, year, esg_urls[:5])
    return sorted_results[0] if sorted_results else None


def _sort_search_results(company_name: str, ticker: str, year: str, search_results: List[str]) -> List[str]:
    scored_results = []
    for url in search_results:
        result_obj = SearchResult(company_name=company_name, ticker=ticker, url=url, year=year)
        score = result_obj.score_search()
        scored_results.append((url, score))

    scored_results.sort(key=lambda x: x[1], reverse=True)
    return [result[0] for result in scored_results]


class SearchResult:
    def __init__(self, company_name: str, ticker: str, url: str, year: str):
        self.company_name = company_name
        self.ticker = ticker
        self.url = url
        self.year = year

    def score_search(self):
        stripped_name = self.company_name.split(" ")[0].lower()
        text_score = self.score_text(self.url.lower())

        if stripped_name not in self.url.lower():
            text_score -= 5
        if self.company_name.lower() in self.url.lower():
            text_score += 1
        if self.ticker.lower() in self.url.lower():
            text_score += 1

        return text_score

    @staticmethod
    def score_text(text: str):
        keywords = ["esg", "sustainability", "report", "environmental", "social", "governance"]
        return sum(keyword in text for keyword in keywords)


if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    ticker = input("Enter the company ticker (or leave blank): ")
    year = input("Enter the year for the ESG report: ")

    best_esg_url = _get_report_search_results(company_name, ticker, year)

    if best_esg_url:
        print(f"\nBest ESG report link: {best_esg_url}")
