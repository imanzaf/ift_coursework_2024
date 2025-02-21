import src.modules.mongo_db.company_data as mongo
import src.modules.minio.minio_script as minio
import src.modules.crawler.crawler as crawler
import src.modules.crawler.crawler_google_api as crawler_google_api
import src.modules.crawler.sustainability_reports_beautifulsoup as sustainability_reports_beautifulsoup
from datetime import datetime
import logging


def populate_reports_sustainability_reports_org(db):
    """Populate all documents with available CSR reports using BeautifulSoup before processing."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    collection = db.companies  # Adjust collection name as needed

    # Loop through each document and populate with available reports
    for document in collection.find():
        company_name = document["security"]
        ticker = document.get("symbol", "")  # Ensure ticker is present if needed
        logger.info(f"Populating CSR reports for company: {company_name}")

        try:
            existing_reports = document.get("csr_reports", {})

            # Fetch CSR reports using BeautifulSoup
            csr_reports = sustainability_reports_beautifulsoup.store_reports_for_company(company_name, ticker)

            if "error" in csr_reports:
                logger.warning(f"No CSR reports found for {company_name}.")
                continue

            # Append the CSR reports to the database if they are available
            update_data = {}
            for year, report_url in csr_reports.items():
                if str(year) not in existing_reports or not existing_reports[str(year)]:
                    update_data.setdefault("csr_reports", {})[str(year)] = report_url

            # Only update if new reports are found
            if update_data.get("csr_reports"):
                update_data["updated_at"] = datetime.utcnow()  # Add timestamp for update
                collection.update_one({"_id": document["_id"]}, {"$set": update_data})
                logger.info(f"Updated CSR report URLs for {company_name}")
            else:
                logger.info(f"No new CSR reports to add for {company_name}.")

        except Exception as e:
            logger.error(f"Error populating CSR reports for {company_name}: {e}")





def retrieve_and_store_csr_reports(db, years):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    collection = db.companies  # Adjust collection name as needed

    current_year = str(datetime.now().year)
    previous_year = str(datetime.now().year - 1)

    for document in collection.find():
        company_name = document["security"]
        ticker = document.get("symbol", "")  # Ensure ticker is present if needed
        logger.info(f"Processing company: {company_name}")

        try:
            years_to_process = set(years)
            update_data = {"updated_at": datetime.utcnow()}

            # Get existing CSR reports if present
            existing_reports = document.get("csr_reports", {})

            for year in years_to_process:
                # Skip if the year already has a CSR report URL
                if str(year) in existing_reports and existing_reports[str(year)]:
                    logger.info(f"Skipping {company_name} for year {year}, report already exists.")
                    continue

                if str(year) in [current_year, previous_year]:
                    result = crawler.process_company(company_name)
                    if result == (None, None, None):
                        logger.warning(f"No valid result found for {company_name} for year {year}")
                        continue
                    webpage_url, pdf_url = result
                    update_data.setdefault("csr_reports", {})[str(year)] = pdf_url
                    update_data["website_url"] = webpage_url
                else:
                    pdf_url = crawler_google_api._get_report_search_results(company_name, ticker, year)
                    update_data.setdefault("csr_reports", {})[str(year)] = pdf_url

            if update_data.get("csr_reports"):  # Only update if new data is found
                collection.update_one({"_id": document["_id"]}, {"$set": update_data})
                logger.info(f"Updated CSR report URLs for {company_name}")
            else:
                logger.info(f"No updates needed for {company_name}.")

        except Exception as e:
            logger.error(f"Error processing {company_name}: {e}")


def upload_csr_reports_to_minio(db, client):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    collection = db.companies

    for document in collection.find():
        try:
            minio.upload_report_to_minio(document, client)
            logger.info(f"Uploaded report for {document.get('security')} to MinIO")
        except Exception as e:
            logger.error(f"Error uploading {document.get('security')}: {e}")


if __name__ == '__main__':
    mongo_client = mongo.connect_to_mongo()
    if mongo_client is None:
        exit(1)

    minio_client = minio.connect_to_minio()
    if minio_client is None:
        exit(1)
    db = mongo_client["csr_reports"]
    populate_reports_sustainability_reports_org(db)
    #mongo.reset_database()
    #user_input_years = input("Enter the years to process (comma-separated): ")
    #years_list = [year.strip() for year in user_input_years.split(",")]


    #retrieve_and_store_csr_reports(db, years_list)
    #upload_csr_reports_to_minio(db, minio_client)
