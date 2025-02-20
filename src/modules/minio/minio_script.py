import os
from minio import Minio
from minio.error import S3Error
from src.modules.mongo_db.company_data import CompanyData, connect_to_mongo  # Importing necessary classes from the other file
import tempfile
import os
import requests

# --- MinIO Connection Setup ---
def connect_to_minio():
    """Connect to the MinIO server."""
    try:
        client = Minio(
            "localhost:9000",  # MinIO server endpoint
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

def upload_report_to_minio(document, client):
    """
    Upload the CSR report from the given document to MinIO in the structured format.
    """
    try:
        # Extract document data
        symbol = document.get("symbol")
        security_name = document.get("security")
        csr_reports = document.get("csr_reports")

        if not symbol or not security_name or not csr_reports:
            print("Invalid document data. Missing required fields.")
            return

        # Iterate over all years in csr_reports and upload each report
        for year, csr_report_url in csr_reports.items():
            # Check if the report URL is valid
            if not csr_report_url:
                print(f"Invalid CSR report URL for {security_name} in {year}. Skipping.")
                continue

            # Create the folder structure
            folder_path = f"csreport/{security_name}/{year}"

            # Check if the folder already contains the report
            try:
                # Check if the report already exists by listing objects in the year subfolder
                objects = client.list_objects(bucket_name="csreport", prefix=f"{security_name}/{year}/", recursive=True)
                report_uploaded = False
                for obj in objects:
                    if csr_report_url.split("/")[-1] in obj.object_name:
                        report_uploaded = True
                        break

                if report_uploaded:
                    print(f"Report for {security_name} in {year} already exists in MinIO. Skipping upload.")
                    continue

            except S3Error as e:
                print(f"Error checking report existence: {e}")
                continue

            # Use tempfile to create a temporary file to store the downloaded report
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                report_name = csr_report_url.split("/")[-1]
                report_file_path = temp_file.name  # The temp file's path

                # Download the CSR report and save it to the temp file
                try:
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
                        object_name=f"{security_name}/{year}/{report_name}",
                        file_path=report_file_path
                    )
                    print(f"Successfully uploaded {report_name} to {folder_path} in MinIO.")

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
    upload_report_to_minio(sample_company.to_dict(), client)

    # --- Test: Add a New CSR Report to MongoDB and Upload to MinIO ---
    # Here we would normally update the MongoDB database with the new CSR report,
    # but for now, we are directly uploading it to MinIO.

    print("Test completed.")


if __name__ == "__main__":
    main()
