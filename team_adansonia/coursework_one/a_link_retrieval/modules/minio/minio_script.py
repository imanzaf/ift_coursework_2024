import os
import tempfile
import requests
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
from ...modules.mongo_db.company_data import connect_to_mongo, CompanyData
from ...modules.utils.dockercheck import is_running_in_docker


# --- MinIO Connection Setup ---
def connect_to_minio():
    """Connect to the MinIO server."""
    try:
        if is_running_in_docker():
            minio_endpoint = "miniocw:9000"
        else:
            minio_endpoint = "localhost:9000"

        print(f"Connecting to MinIO at {minio_endpoint}")
        
        client = Minio(
            minio_endpoint,  # MinIO server endpoint
            access_key="ift_bigdata",
            secret_key="minio_password",
            secure=False  # Set to True if you use HTTPS
        )
        # Check if the bucket exists, otherwise create it
        if not client.bucket_exists("csreport"):
            client.make_bucket("csreport")
            print("✅ Created 'csreport' bucket.")
        else:
            print("✅ 'csreport' bucket already exists.")
        return client
    except S3Error as e:
        print(f"❌ Error connecting to MinIO: {e}")
        return None


def upload_report_to_minio(document, client, mongo_client):
    """
    Upload CSR reports to MinIO and update the MongoDB document with MinIO URLs.
    """
    try:
        # Extract necessary document data
        symbol = document.get("symbol")
        security_name = document.get("security")
        csr_reports = document.get("csr_reports")
        document_id = document.get("_id")  # Ensure the document contains its _id

        if not symbol or not security_name or not csr_reports or not document_id:
            print("Invalid document data. Missing required fields.")
            return

        # Dictionary to hold MinIO URLs for each year
        minio_urls = {}

        # Iterate over all years in csr_reports and upload each report
        for year, csr_report_url in csr_reports.items():
            if not csr_report_url:
                print(f"Invalid CSR report URL for {security_name} in {year}. Skipping.")
                continue

            # Create the object name for MinIO
            object_name = f"{security_name}/{year}/{csr_report_url.split('/')[-1]}"

            try:
                # Check if the report already exists
                try:
                    client.stat_object("csreport", object_name)
                    print(f"Report for {security_name} in {year} already exists in MinIO. Skipping upload.")
                    continue  # Skip upload if the report already exists
                except S3Error as e:
                    if e.code != 'NoSuchKey':
                        print(f"Error checking report existence: {e}")
                        continue  # Skip the upload if there's an error other than 'NoSuchKey'

                # Use tempfile to create a temporary file to store the downloaded report
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    report_file_path = temp_file.name  # The temp file's path

                try:
                    # Download the CSR report and save it to the temp file
                    response = requests.get(csr_report_url, stream=True)
                    if response.status_code == 200:
                        with open(report_file_path, 'wb') as file:
                            for chunk in response.iter_content(1024):
                                file.write(chunk)
                    else:
                        print(f"Failed to download report: {csr_report_url}")
                        continue

                    # Upload the report to MinIO
                    client.fput_object(
                        bucket_name="csreport",
                        object_name=object_name,
                        file_path=report_file_path
                    )
                    print(f"Successfully uploaded {object_name} to MinIO.")

                    # Generate a presigned URL valid for 7 days
                    presigned_url = client.presigned_get_object(
                        "csreport",
                        object_name,
                        expires=timedelta(days=7)
                    )

                    # Add the presigned URL to the dictionary
                    minio_urls[year] = presigned_url

                except requests.RequestException as e:
                    print(f"Error downloading report: {e}")
                finally:
                    # Clean up the temporary file
                    if os.path.exists(report_file_path):
                        os.remove(report_file_path)

            except S3Error as e:
                print(f"MinIO S3Error: {e}")
            except Exception as e:
                print(f"Error: {e}")

        # Update the MongoDB document with the dictionary of MinIO URLs
        if minio_urls:
            db = mongo_client["csr_reports"]  # Replace with your database name
            collection = db['companies']  # Replace with your collection name
            collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"minio_urls": minio_urls}}
            )
            print(f"Updated MongoDB document with MinIO URLs: {minio_urls}")

    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    # Sample company data with CSR report for Microsoft
    sample_company = CompanyData(
        symbol="MSFT",
        security="Microsoft Corp.",
        gics_sector="Information Technology",
        gics_industry="Systems Software",
        country="US",
        region="North America",
        csr_reports={  # Notice the csr_reports dictionary
            "2024": "https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/msc/documents/presentations/CSR/Microsoft-2024-Environmental-Sustainability-Report.pdf"
        }
    )

    # --- MongoDB Setup ---
    mongo_client = connect_to_mongo()  # Connect to MongoDB
    if mongo_client is None:
        exit(1)  # Exit if MongoDB is not connected

    # --- MinIO Setup ---
    client = connect_to_minio()  # Connect to MinIO
    if client is None:
        exit(1)  # Exit if MinIO is not connected

    # --- Upload CSR Reports to MinIO ---
    upload_report_to_minio(sample_company.to_dict(), client, mongo_client)

    # --- Test: Add a New CSR Report to MongoDB and Upload to MinIO ---
    # Here we would normally update the MongoDB database with the new CSR report,
    # but for now, we are directly uploading it to MinIO.

    print("Test completed.")


if __name__ == "__main__":
    main()
