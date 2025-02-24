from minio import Minio
import yaml
import os

# Get the current working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config', 'conf.yaml')

# Load config file
try:
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Config file not found at {config_path}. Please ensure it's in the correct directory.")
    raise


def get_minio_client():
    """Connect to MinIO and return the client."""
    minio_client = Minio(
        config["minio"]["endpoint"],
        access_key=config["minio"]["access_key"],
        secret_key=config["minio"]["secret_key"],
        secure=False
    )

    bucket_name = config["minio"]["bucket_name"]
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        print(f"Created MinIO bucket: {bucket_name}")
    else:
        print(f"Connected to MinIO bucket: {bucket_name}")

    return minio_client


minio_client = get_minio_client()

MINIO_CONFIG = config["minio"]
BUCKET_NAME = MINIO_CONFIG["bucket_name"]

# Ensure bucket exists
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)

def upload_to_minio(local_pdf_path, company_symbol, report_year):
    """Uploads a file to MinIO with a structured path."""
    minio_pdf_path = f"{company_symbol}/{report_year}"
    minio_client.fput_object(BUCKET_NAME, minio_pdf_path, local_pdf_path)

    return f"http://{MINIO_CONFIG['endpoint']}/{BUCKET_NAME}/{minio_pdf_path}"



