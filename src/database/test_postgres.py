# test_postgres.py
import sys
import os
from loguru import logger

# If needed, add the parent directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from postgres import PostgreSQLDB

def main():
    logger.info("Testing PostgreSQLDB...")

    # 1. Instantiate the Postgres class (context manager style)
    with PostgreSQLDB() as pg:
        logger.info("Connection established.")

        # 2. Test an INSERT
        logger.info("Testing store_csr_report...")
        pg.store_csr_report(company_id=1, report_url="http://test-url.com", report_year=2024)

        # 3. Test a SELECT
        logger.info("Testing get_csr_reports_by_company...")
        results = pg.get_csr_reports_by_company(1)
        logger.info(f"Results for company=1: {results}")

        # 4. Test update & fetch by ID, if needed
        # Suppose you know the new row's 'report_id' is 10 (or you can fetch it from results)
        # This is purely an example:
        # pg.update_csr_report(report_id=10, new_url="http://new-url.com")
        # updated_record = pg.get_csr_report_by_id(10)
        # logger.info(f"Updated record #10: {updated_record}")

if __name__ == "__main__":
    main()
