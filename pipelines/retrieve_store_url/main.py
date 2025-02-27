"""
retrieve_store_url/main.py

For each company in csr_reporting.company_static:
  1) Use Google & SustainabilityReports.com to find best ESG/CSR report URLs
  2) Store them in csr_reporting.company_csr_reports
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from loguru import logger
from src.data_models.company import Company
from src.database.postgres import PostgreSQLDB
from src.esg_reports.search import Search
from src.esg_reports.validate import SearchResultValidator


def main():
    logger.info("Starting retrieve_store_url pipeline...")

    with PostgreSQLDB() as db:
        # 1) Fetch companies from csr_reporting.company_static
        rows = db.fetch_all_companies()
        if not rows:
            logger.error("No companies found in csr_reporting.company_static. Exiting.")
            return

        logger.info(f"Found {len(rows)} companies in company_static.")

        for row in rows:
            symbol = row["symbol"].strip()  # Because it's CHAR(12)
            security = row["security"]

            company = Company(
                symbol=symbol,
                security=security,
                gics_sector=row["gics_sector"],
                gics_industry=row["gics_industry"],
                country=row["country"],
                region=row["region"],
            )

            # 2) Search for ESG reports (Google + responsibilityreports.com)
            search_instance = Search(company=company)
            google_results = search_instance.google()
            sustainability_result = search_instance.sustainability_reports_dot_com()

            # Validate google results
            best_google_url = None
            if google_results:
                validator = SearchResultValidator(company=company, search_results=google_results)
                valid_google_results = validator.validated_results
                if valid_google_results:
                    best_google_url = valid_google_results[0].link
                else:
                    logger.warning(f"[{security}] No valid Google search results found.")
            else:
                logger.warning(f"[{security}] No Google results found at all.")

            # Possibly from sustainability
            best_sustain_url = sustainability_result.url if sustainability_result else None

            logger.info(f"\n=== {security} ESG report links ===")
            if best_google_url:
                logger.info(f"  Google: {best_google_url}")
            if best_sustain_url:
                logger.info(f"  SustainabilityReports.com: {best_sustain_url}")

            # 3) Insert or update in company_csr_reports table
            # We'll store them with a default year, say 2024 for google, 2023 for sustain, or you might parse the year from the results
            if best_google_url:
                db.store_csr_report(symbol, best_google_url, 2024)
            if best_sustain_url and sustainability_result.year:
                db.store_csr_report(symbol, best_sustain_url, sustainability_result.year)
            else:
                # If no year from sustain, default to 2023
                if best_sustain_url:
                    db.store_csr_report(symbol, best_sustain_url, 2023)

            logger.info(f"[{security}] done storing CSR links in company_csr_reports.\n")

    logger.info("retrieve_store_url pipeline completed.")


if __name__ == "__main__":
    main()
