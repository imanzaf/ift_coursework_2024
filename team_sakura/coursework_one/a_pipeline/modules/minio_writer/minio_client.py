from minio import Minio
import yaml
import os
from minio.error import S3Error

config_path = os.getenv("CONF_PATH", "/app/config/conf.yaml")  # Default path for Docker
with open(config_path, "r") as file:
    config = yaml.safe_load(file)


def get_minio_client():
    # Ensure the service name "miniocw" is used inside the Docker network
    minio_host = os.getenv("MINIO_HOST", "miniocw:9000")  # Update this!
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "ift_bigdata")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minio_password")

    minio_client = Minio(
        minio_host,
        access_key=access_key,
        secret_key=secret_key,
        secure=False  # Set to False if using HTTP
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


def delete_all_files_from_minio():
    try:
        # List all objects in the bucket
        objects = minio_client.list_objects(BUCKET_NAME, recursive=True)

        for obj in objects:
            minio_client.remove_object(BUCKET_NAME, obj.object_name)
            print(f"Deleted {obj.object_name}")

    except S3Error as e:
        print(f"Error while deleting from Minio: {e}")


# delete_all_files_from_minio() to call if you want to delete all files from minio


def upload_to_minio(local_pdf_path, company_symbol, report_year):
    """Uploads a file to MinIO with a structured path."""
    minio_pdf_path = f"{company_symbol}/{report_year}"
    minio_client.fput_object(BUCKET_NAME, minio_pdf_path, local_pdf_path)

    return f"http://{MINIO_CONFIG['endpoint']}/{BUCKET_NAME}/{minio_pdf_path}"



