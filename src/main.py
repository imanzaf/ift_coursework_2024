import logging
from datetime import datetime

import urllib3

import src.modules.mongo_db.company_data as mongo
import src.modules.minio.minio_script as minio
import src.modules.crawler.crawler as crawler

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def process_and_upload_documents(db, client, year):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    collection = db.companies  # Adjust collection name as needed

    for document in collection.find():
        company_name = document["security"]
        logger.info(f"Processing company: {company_name}")

        try:
            # Call the crawler function
            result = crawler.process_company(company_name)
            if result == (None, None, None):  # If no valid result is returned
                logger.warning(f"No valid result found for {company_name}")
                continue
            print(f"DEBUG: process_company({company_name}) returned {result}")
            webpage_url, pdf_url = result
            logger.info(f"Retrieved webpage URL: {webpage_url}")

            # Initialize update_data if csr_reports doesn't exist or is empty
            update_data = {
                "website_url": webpage_url,
                "updated_at": datetime.utcnow()
            }

            if "csr_reports" not in update_data or not update_data["csr_reports"]:
                update_data["csr_reports"] = {year: pdf_url}  # Add year as key and pdf_url as value
            else:
                update_data["csr_reports"][year] = pdf_url  # If csr_reports exists, update it with the new year

            print(update_data)

            # Update the document
            collection.update_one({"_id": document["_id"]}, {"$set": update_data})
            logger.info(f"Updated document for {company_name}")

            # Upload the updated document to MinIO
            minio.upload_report_to_minio(document, client)
            logger.info(f"Uploaded report for {company_name} to MinIO")

        except Exception as e:
            logger.error(f"Error processing {company_name}: {e}")
            continue


if __name__ == '__main__':
    mongo_client = mongo.connect_to_mongo()
    mongo_client = mongo.connect_to_mongo()  # Connect to MongoDB
    if mongo_client is None:
        exit(1)  # Exit if MongoDB is not connected
    mongo.import_seed_to_mongo()
    minio_client = minio.connect_to_minio()  # Connect to MinIO
    if minio_client is None:
        exit(1)

    # Initialize your MinIO client accordingly
    year = "2024"  # Replace with the actual year input
    db = mongo_client["csr_reports"]
    process_and_upload_documents(db, minio_client, year)
