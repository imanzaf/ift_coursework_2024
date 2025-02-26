import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger
from database.postgres import PostgreSQLDB
from src.data_models.company import Company, ESGReport, SearchResult
from src.esg_reports.search import Search
from src.esg_reports.validate import SearchResultValidator

def main():
    with PostgreSQLDB() as db:
        companies = db.fetch("SELECT id, name FROM companies")
        if not companies:
            logger.error("No companies found in the database.")
            return
        for company_data in companies:
            company_id = company_data["id"]
            company_name = company_data["name"]
            company = Company(
                symbol="",  
                security=company_name,
                gics_sector="",
                gics_industry="",
                country="",
                region=""
            )
            search_instance = Search(company=company)
            google_results = search_instance.google()
            if google_results:
                validator = SearchResultValidator(company=company, search_results=google_results)
                valid_google_results = validator.validated_results
                if valid_google_results:
                    google_best = valid_google_results[0]
                else:
                    google_best = None
                    logger.warning(f"[{company_name}] The Google search results did not pass validation.")
            else:
                google_best = None
                logger.warning(f"[{company_name}] No Google search results were found.")
            sustainability_result = search_instance.sustainability_reports_dot_com()
            google_url = google_best.link if google_best else None
            responsibilityreport_url = (
                sustainability_result.url 
                if (sustainability_result and sustainability_result.url) 
                else None
            )
            print(f"\n=== {company_name} ESG report search results ===\n")
            if google_url:
                print(f"[Google API] Latest ESG report link: {google_url}")
            else:
                print("[Google API] No ESG report link found that meets the criteria.")
            if responsibilityreport_url:
                print(f"[SustainabilityReports.com] Latest ESG report link: {responsibilityreport_url} (Year: {sustainability_result.year})")
            else:
                print("[SustainabilityReports.com] No valid ESG report link found.")
            update_query = """
                UPDATE companies
                SET google_url = %s,
                    responsibilityreport_url = %s
                WHERE id = %s
            """
            db.execute(update_query, (google_url, responsibilityreport_url, company_id))
            logger.info(f"[{company_name}] The retrieved links have been written to the database.")

if __name__ == "__main__":
    main()
