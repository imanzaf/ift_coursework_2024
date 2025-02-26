import os
import sys

from loguru import logger

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.data_models.company import Company, ESGReport
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


def get_validated_results(company: Company) -> Company:
    """
    Get validated search results for each company.
    """
    # Search for ESG reports for the company.
    search_instance = Search(company=company)
    company_name = company.security
    google_results = search_instance.google()
    sust_report_result = search_instance.sustainability_reports_dot_com()

    # Validate the google search results.
    if google_results:
        validator = SearchResultValidator(
            company=company, search_results=google_results
        )
        valid_google_results = validator.validated_results
        if valid_google_results:
            google_result = valid_google_results[0]
        else:
            google_result = ESGReport(url=None, year=None)
            logger.warning(f"[{company_name}] No valid Google search results found.")
    else:
        google_result = ESGReport(url=None, year=None)
        logger.warning(f"[{company_name}] No Google search results were found.")

    # Log the search results.
    logger.debug(f"\n=== {company_name} ESG report search results ===\n")
    if google_result:
        logger.debug(f"[Google API] Latest ESG report: {google_result}")
    else:
        logger.debug("[Google API] No ESG report link found that meets the criteria.")
    if sust_report_result:
        logger.debug(
            f"[SustainabilityReports.com] Latest ESG report: {sust_report_result})"
        )
    else:
        logger.debug("[SustainabilityReports.com] No valid ESG report link found.")

    company.esg_reports = [google_result, sust_report_result]
    return company


def update_db(db: PostgreSQLDB, company: Company):
    """
    Update the database with the latest ESG report links.
    """
    urls = {}
    esg_reports = company.esg_reports
    if esg_reports[0].year == esg_reports[1].year:
        urls.update(
            {
                (
                    esg_reports[0].year if esg_reports[0].year is not None else "Other"
                ): esg_reports[0].url
            }
        )
    else:
        urls.update(
            {
                (
                    esg_reports[0].year if esg_reports[0].year is not None else "Other"
                ): esg_reports[0].url
            }
        )
        urls.update(
            {
                (
                    esg_reports[1].year if esg_reports[1].year is not None else "Other"
                ): esg_reports[1].url
            }
        )

    update_query = """
    INSERT INTO company_data (company_name, ":year")
    VALUES (:company_name, :url)
    ON CONFLICT (company_name)
    DO UPDATE SET ":year" = EXCLUDED.":year";
    """
    db.execute(
        update_query,
        {
            "company_name": company.security,
            "year": esg_reports[0].year,
            "url": esg_reports[0].url,
        },
    )
    db.execute(
        update_query,
        {
            "company_name": company.security,
            "year": esg_reports[1].year,
            "url": esg_reports[1].url,
        },
    )
    logger.info(
        f"[{company.security}] The retrieved links have been written to the database."
    )


def main():
    with PostgreSQLDB() as db:
        # Create new table
        query = """
        CREATE TABLE IF NOT EXISTS scr_reporting.company_urls (
        company_name VARCHAR(255) NOT NULL,
        "2025" STRING
        "2024" STRING,
        "2023" STRING,
        "2022" STRING,
        "Other" STRING
        );
        """
        db.execute(query)
        logger.info("Created the company_urls table.")

        companies = get_all_companies(db)
        logger.info(f"Retrieved {len(companies)} companies from the database.")
        for company in companies:
            company = get_validated_results(company)
            update_db(db, company)
            logger.info(
                f"[{company.security}] Updated the database with the latest ESG report links."
            )
        logger.info("All companies have been processed.")


if __name__ == "__main__":
    main()
