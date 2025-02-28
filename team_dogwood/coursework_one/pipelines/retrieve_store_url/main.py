import os
import sys

from loguru import logger

# from sqlalchemy.sql import text

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.data_models.company import Company, ESGReport
from src.database.postgres import PostgreSQLDB
from src.esg_reports.search import Search
from src.esg_reports.validate import SearchResultValidator


def get_all_companies(db: PostgreSQLDB) -> list[Company]:
    """
    Get all companies from the database.
    """
    companies = db.fetch("SELECT symbol, security FROM csr_reporting.company_static")
    logger.debug(f"Companies Preview: {companies[:1]}")
    if not companies:
        logger.error("No companies found in the database. Exiting.")
        exit()

    companies_list = []
    for company_data in companies:
        logger.info(f"Processing company: {company_data['security']}")
        company = Company(**company_data)
        companies_list.append(company)

    return companies_list


def get_validated_results(company: Company) -> Company:
    """
    Get validated search results for each company.

    TODO - only intialize webdriver once and pass it to the search instance.
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
    if esg_reports[0].year == esg_reports[1].year and esg_reports[0].url is not None:
        urls.update({(esg_reports[0].year): esg_reports[0].url})
    else:
        if esg_reports[0].url is not None:
            urls.update({(esg_reports[0].year): esg_reports[0].url})
        if esg_reports[1].url is not None:
            urls.update({(esg_reports[1].year): esg_reports[1].url})

    update_query = """
    INSERT INTO csr_reporting.company_csr_reports (company_name, report_url, report_year, retrieved_at)
    VALUES (%s, %s, %s, NOW())
    ON CONFLICT (company_name, report_year)
    DO UPDATE SET "report_url" = EXCLUDED.report_url, "retrieved_at" = NOW();
    """
    for item in urls.items():
        db.execute(update_query, (company.security, item[1], item[0]))
    logger.info(
        f"[{company.security}] The retrieved links have been written to the database."
    )


def main():
    with PostgreSQLDB() as db:
        # Create new table
        query = """
        CREATE TABLE IF NOT EXISTS csr_reporting.company_csr_reports (
        company_name VARCHAR(255) NOT NULL,
        report_url VARCHAR(255) NOT NULL,
        report_year INT,
        retrieved_at TIMESTAMP DEFAULT NOW(),
        PRIMARY KEY (company_name, report_year)
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
