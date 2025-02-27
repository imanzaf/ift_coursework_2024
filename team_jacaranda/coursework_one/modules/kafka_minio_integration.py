import io
import json
import requests
import time
from kafka import KafkaConsumer
from minio import Minio
from minio.error import S3Error
import psycopg2

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'csr-report'

# MinIO configuration
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'ift_bigdata'
MINIO_SECRET_KEY = 'minio_password'
MINIO_BUCKET = 'csreport'

# PostgreSQL configuration
PG_HOST = 'host.docker.internal'
PG_PORT = 5439
PG_DB = 'fift'
PG_USER = 'postgres'
PG_PASSWORD = 'postgres'

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

# Initialize Kafka consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Connect to PostgreSQL
def connect_to_postgres():
    print("Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        print("Successfully connected to PostgreSQL!")
        return conn
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        raise

# Download PDF file with timeout handling
def download_pdf(url):
    print(f"Downloading PDF from {url}...")
    try:
        start_time = time.time()
        response = requests.get(url, timeout=60)
        elapsed_time = time.time() - start_time

        if response.status_code == 200 and elapsed_time <= 60:
            print(f"Successfully downloaded PDF from {url}")
            return response.content
        else:
            raise Exception(f"Failed to download PDF from {url}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading PDF from {url}: {e}")
        raise

# Upload PDF file to MinIO
def upload_to_minio(file_name, file_data):
    print(f"Uploading {file_name} to MinIO...")
    try:
        # Debug information: print file_data type and length
        print(f"File data type: {type(file_data)}")
        print(f"File data length: {len(file_data)}")

        # Convert bytes object to BytesIO object
        file_stream = io.BytesIO(file_data)

        # Upload file to MinIO
        minio_client.put_object(
            MINIO_BUCKET,
            file_name,
            file_stream,  # Use file stream object
            length=len(file_data),
            content_type='application/pdf'
        )
        print(f"Successfully uploaded {file_name} to MinIO bucket {MINIO_BUCKET}")
    except S3Error as e:
        print(f"Failed to upload {file_name} to MinIO: {e}")
        raise

# Main logic
def main():
    print("Starting Kafka-MinIO integration script...")
    conn = connect_to_postgres()
    cursor = conn.cursor()

    print(f"Listening for messages on Kafka topic '{KAFKA_TOPIC}'...")
    for message in consumer:
        print("\n--- Processing new message ---")
        data = message.value
        company_name = data['company_name']
        report_urls = data['report_urls']

        print(f"Processing company: {company_name}")
        print(f"Found {len(report_urls)} report URLs")

        for url in report_urls:
            try:
                print(f"\nProcessing URL: {url}")

                # Download PDF file
                pdf_data = download_pdf(url)

                # Fetch security and report_year from PostgreSQL
                cursor.execute(
                    "SELECT security, report_year FROM csr_reporting.company_reports WHERE report_url = %s",
                    (url,)
                )
                result = cursor.fetchone()
                if result:
                    security, report_year = result
                    file_name = f"{security}_{report_year}.pdf"
                else:
                    raise Exception(f"No matching record found for URL: {url}")

                print(f"Generated file name: {file_name}")

                # Upload to MinIO
                upload_to_minio(file_name, pdf_data)

                # Record upload status in PostgreSQL
                print(f"Recording upload status in PostgreSQL for {file_name}...")
                cursor.execute(
                    "UPDATE csr_reporting.company_reports SET minio_path = %s WHERE report_url = %s",
                    (file_name, url)
                )
                conn.commit()
                print(f"Successfully updated minio_path for {file_name} in PostgreSQL")
            except Exception as e:
                print(f"Error processing {url}: {e}")
                # Record download failure in PostgreSQL
                cursor.execute(
                    "UPDATE csr_reporting.company_reports SET minio_path = %s WHERE report_url = %s",
                    ("download_failed", url)
                )
                conn.commit()
                print(f"Recorded download failure for {url} in PostgreSQL")

    cursor.close()
    conn.close()
    print("Script finished.")

if __name__ == "__main__":
    main()
