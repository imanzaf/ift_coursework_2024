"""
MinIO Upload Module

This module handles the upload of CSR report PDFs to MinIO storage.
It includes functionality for connecting to MinIO, creating buckets,
and uploading files with appropriate metadata.
"""

import os
import boto3
import psycopg2
import datetime
import pandas as pd
from botocore.exceptions import NoCredentialsError

def get_config():
    """
    Get configuration settings from environment variables.
    
    Returns:
        dict: Configuration settings
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    config = {
        'source_csv_path': os.getenv(
            "SOURCE_CSV", 
            os.path.join(base_dir, "a_pipeline", "aresult", "cleaned_url.csv")
        ),
        'local_folder': os.getenv(
            "CSR_REPORTS_PATH", 
            os.path.join(base_dir, "b_pipeline", "bresult", "csr_reports")
        ),
        'minio': {
            'endpoint': os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
            'access_key': os.getenv("MINIO_ACCESS_KEY", "ift_bigdata"),
            'secret_key': os.getenv("MINIO_SECRET_KEY", "minio_password"),
            'bucket_name': os.getenv("MINIO_BUCKET", "csr-reports")
        },
        'postgres': {
            'host': os.getenv("POSTGRES_HOST", "localhost"),
            'port': os.getenv("POSTGRES_PORT", "5439"),
            'database': os.getenv("POSTGRES_DB", "fift"),
            'user': os.getenv("POSTGRES_USER", "postgres"),
            'password': os.getenv("POSTGRES_PASSWORD", "postgres")
        }
    }
    
    # Adjust PostgreSQL host and port for Docker environment
    if os.getenv("RUN_ENV") == "docker":
        config['postgres']['host'] = "postgres_db_cw"
        config['postgres']['port'] = "5432"
    
    return config

def create_minio_client(config):
    """
    Create a MinIO client using the provided configuration.
    
    Args:
        config (dict): Configuration dictionary containing MinIO settings
        
    Returns:
        boto3.client: Configured MinIO client
    """
    return boto3.client(
        "s3",
        endpoint_url=config['minio']['endpoint'],
        aws_access_key_id=config['minio']['access_key'],
        aws_secret_access_key=config['minio']['secret_key']
    )

def sanitize_name(name):
    """
    Sanitize storage name by removing invalid characters.
    
    Args:
        name (str): Original name to sanitize
        
    Returns:
        str: Sanitized name suitable for MinIO storage
    """
    return name.replace("'", "").replace(".", "").replace(",", "").replace(" ", "_")

def insert_into_db(config, security, report_year, minio_url, source_url):
    """
    Insert or update CSR report record in PostgreSQL database.
    
    Args:
        config (dict): Configuration dictionary containing database settings
        security (str): Company security identifier
        report_year (int): Report year
        minio_url (str): URL to the report in MinIO storage
        source_url (str): Original source URL of the report
        
    Returns:
        None
    """
    try:
        conn = psycopg2.connect(
            host=config['postgres']['host'],
            port=config['postgres']['port'],
            database=config['postgres']['database'],
            user=config['postgres']['user'],
            password=config['postgres']['password']
        )
        cursor = conn.cursor()

        # Create schema and table if they don't exist
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS csr_reporting;
            
            CREATE TABLE IF NOT EXISTS csr_reporting.csr_reports (
                "id" SERIAL PRIMARY KEY,
                "security" TEXT NOT NULL,
                "report_year" INTEGER NOT NULL,
                "minio_path" TEXT NOT NULL,
                "source_url" TEXT,
                "ingestion_timestamp" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE("security", "report_year")
            );
        """)
        conn.commit()

        cursor.execute("SELECT security FROM csr_reporting.company_static WHERE security = %s;", (security,))
        result = cursor.fetchone()

        if not result:
            # If company doesn't exist in company_static, create it
            cursor.execute("""
                INSERT INTO csr_reporting.company_static (security) 
                VALUES (%s) 
                ON CONFLICT DO NOTHING
            """, (security,))
            conn.commit()

        ingestion_timestamp = datetime.datetime.now()

        cursor.execute("""
            INSERT INTO csr_reporting.csr_reports (security, report_year, minio_path, source_url, ingestion_timestamp)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (security, report_year)
            DO UPDATE SET 
                minio_path = EXCLUDED.minio_path, 
                source_url = EXCLUDED.source_url, 
                ingestion_timestamp = EXCLUDED.ingestion_timestamp;
        """, (security, report_year, minio_url, source_url, ingestion_timestamp))

        conn.commit()
        conn.close()
        print(f"✅ Successfully recorded in PostgreSQL: {security} - {report_year}")

    except Exception as e:
        print(f"❌ PostgreSQL Error: {str(e)}")

def upload_to_minio(config, s3_client, file_path, security, report_year, df_sources=None):
    """
    Upload a file to MinIO storage.
    
    Args:
        config (dict): Configuration dictionary
        s3_client: MinIO client instance
        file_path (str): Path to the file to upload
        security (str): Company security identifier
        report_year (int): Report year
        df_sources (pd.DataFrame, optional): DataFrame containing source URLs
        
    Returns:
        None
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    file_name = os.path.basename(file_path)
    safe_security = sanitize_name(security)
    minio_path = f"{safe_security}/{report_year}/{file_name}"

    source_url = None
    if df_sources is not None:
        match = df_sources[(df_sources['company'] == security) & (df_sources['year'] == report_year)]
        if not match.empty:
            source_url = match.iloc[0]['url']

    try:
        s3_client.upload_file(file_path, config['minio']['bucket_name'], minio_path)
        minio_url = f"{config['minio']['endpoint']}/{config['minio']['bucket_name']}/{minio_path}"
        print(f"📤 Upload successful: {minio_url}")

        insert_into_db(config, security, report_year, minio_url, source_url)

    except NoCredentialsError:
        print("❌ Cannot access MinIO, please check credentials!")

def main():
    """
    Main function to process and upload CSR reports to MinIO.
    
    This function:
    1. Loads configuration
    2. Creates MinIO client
    3. Reads source URLs if available
    4. Processes and uploads PDF files
    5. Updates database records
    
    Returns:
        None
    """
    config = get_config()
    
    # Normalize paths
    config['source_csv_path'] = os.path.normpath(config['source_csv_path'])
    config['local_folder'] = os.path.normpath(config['local_folder'])
    
    print(f"Looking for CSV at: {config['source_csv_path']}")
    print(f"Looking for PDF files in: {config['local_folder']}")
    
    # Read source URLs if available
    df_sources = None
    if os.path.exists(config['source_csv_path']):
        df_sources = pd.read_csv(config['source_csv_path'])
        print(f"✅ Successfully loaded cleaned_url.csv, total {len(df_sources)} records")
        print(f"CSV columns: {df_sources.columns.tolist()}")
    else:
        print(f"⚠️ Cannot find cleaned_url.csv, skipping URL records!")
    
    # Create MinIO client
    s3_client = create_minio_client(config)
    
    if not os.path.exists(config['local_folder']):
        print("❌ Folder does not exist, please check if files are downloaded!")
        return
    
    print("✅ Reading local CSR reports folder...")
    
    for security in os.listdir(config['local_folder']):
        security_path = os.path.join(config['local_folder'], security)
        
        if not os.path.isdir(security_path):
            continue
            
        for year in os.listdir(security_path):
            year_path = os.path.join(security_path, year)
            
            if not os.path.isdir(year_path):
                continue
                
            if not year.isdigit():
                print(f"⚠️ Found non-numeric year `{year}`, skipping...")
                continue
                
            report_year = int(year)
            
            for file_name in os.listdir(year_path):
                if file_name.lower().endswith(".pdf"):
                    file_path = os.path.normpath(os.path.join(year_path, file_name))
                    print(f"📤 Uploading report `{file_name}` for {security} {report_year}...")
                    upload_to_minio(config, s3_client, file_path, security, report_year, df_sources)
                    print(f"✅ {file_name} upload completed!")
    
    print("🎉 All files have been processed!")

if __name__ == "__main__":
    main()
