import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from loguru import logger

from src.data_models.company import Company  # ESGReport, SearchResult
from src.database.postgres import PostgreSQLDB
from src.esg_reports.search import Search
from src.esg_reports.validate import SearchResultValidator


def get_all_companies(db: PostgreSQLDB) -> list[Company]:
    """
    Get all companies from the database.
    """
    companies = db.execute(
        "SELECT symbol, security FROM csr_reporting.company_static WHERE security = 'MMM'"
    )
    logger.info(f"Companies: {companies[:5]}")
    if not companies:
        logger.error("No companies found in the database. Exiting.")
        exit()

    companies_list = []
    for company_data in companies:
        company = Company(**company_data)
        companies_list.append(company)

    return companies_list


def get_validated_results(company: Company):
    """
    Get validated search results for each company.
    """
    # Search for ESG reports for the company.
    search_instance = Search(company=company)
    company_name = company.security
    google_results = search_instance.google()
    sustainability_result = search_instance.sustainability_reports_dot_com()

    # Validate the google search results.
    if google_results:
        validator = SearchResultValidator(
            company=company, search_results=google_results
        )
        valid_google_results = validator.validated_results
        if valid_google_results:
            google_best = valid_google_results[0]
        else:
            google_best = None
            logger.warning(f"[{company_name}] No valid Google search results found.")
    else:
        google_best = None
        logger.warning(f"[{company_name}] No Google search results were found.")

    google_url = google_best.link if google_best else None
    sust_report_url = sustainability_result.url if sustainability_result else None

    # Log the search results.
    logger.debug(f"\n=== {company_name} ESG report search results ===\n")
    if google_url:
        logger.debug(f"[Google API] Latest ESG report link: {google_url}")
    else:
        logger.debug("[Google API] No ESG report link found that meets the criteria.")
    if sust_report_url:
        logger.debug(
            f"[SustainabilityReports.com] Latest ESG report link: {sust_report_url} (Year: {sustainability_result.year})"
        )
    else:
        logger.debug("[SustainabilityReports.com] No valid ESG report link found.")

    return google_url, sust_report_url


def update_db(
    db: PostgreSQLDB, company: Company, google_url: str, sust_report_url: str
):
    update_query = """
    UPDATE csr_reporting.company_static
    SET google_url = %s,
        responsibilityreport_url = %s
    WHERE security = %s
    """
    db.execute(update_query, (google_url, sust_report_url, company.security))
    logger.info(
        f"[{company.security}] The retrieved links have been written to the database."
    )


def main():
    with PostgreSQLDB() as db:
        companies = get_all_companies(db)
        logger.info(f"Retrieved {len(companies)} companies from the database.")
        for company in companies:
            google_url, sust_report_url = get_validated_results(company)
            update_db(db, company, google_url, sust_report_url)
            logger.info(
                f"[{company.security}] Updated the database with the latest ESG report links."
            )
        logger.info("All companies have been processed.")


if __name__ == "__main__":
    main()
