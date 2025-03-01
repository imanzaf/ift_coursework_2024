from minio import Minio
import yaml
import os
from minio.error import S3Error

# Load configuration from YAML file
config_path = os.getenv("CONF_PATH", "a_pipeline/config/conf.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# Determine MinIO configuration based on environment (Docker or local)
if os.getenv("DOCKER_ENV"):
    minio_config = config["miniodocker"]
else:
    minio_config = config["miniolocal"]


def get_minio_client():
    """
    Create and return a MinIO client instance.

    Returns:
        Minio: A configured MinIO client.
    """
    # Ensure the service name "miniocw" is used inside the Docker network
    if os.getenv("DOCKER_ENV"):  # Running in Jenkins or Docker
        minio_host = os.getenv("MINIO_HOST", "miniocw:9000")
    else:  # Running locally
        minio_host = os.getenv("MINIO_HOST", "localhost:9000")

    access_key = os.getenv("AWS_ACCESS_KEY_ID", "ift_bigdata")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minio_password")

    minio_client = Minio(
        minio_host,
        access_key=access_key,
        secret_key=secret_key,
        secure=False,  # Set to False if using HTTP
    )

    bucket_name = minio_config["bucket_name"]
    # Ensure the bucket exists before performing operations
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        print(f"Created MinIO bucket: {bucket_name}")
    else:
        print(f"Connected to MinIO bucket: {bucket_name}")

    return minio_client


# Initialize MinIO client
minio_client = get_minio_client()

BUCKET_NAME = minio_config["bucket_name"]

# Ensure the bucket exists before any operations
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)


def delete_all_files_from_minio():
    """
    Deletes all files from the MinIO bucket.
    """
    try:
        # List all objects in the bucket and remove them
        objects = minio_client.list_objects(BUCKET_NAME, recursive=True)

        for obj in objects:
            minio_client.remove_object(BUCKET_NAME, obj.object_name)
            print(f"Deleted {obj.object_name}")

    except S3Error as e:
        print(f"Error while deleting from MinIO: {e}")


# Call delete_all_files_from_minio() if you want to remove all files from MinIO


def upload_to_minio(local_pdf_path, company_symbol, report_year):
    """
    Uploads a file to MinIO with a structured path.

    Args:
        local_pdf_path (str): Path of the local PDF file to upload.
        company_symbol (str): Company symbol for file categorization.
        report_year (str): Year of the report.

    Returns:
        str: The MinIO URL where the file is stored.
    """
    minio_pdf_path = f"{company_symbol}/{report_year}"
    minio_client.fput_object(BUCKET_NAME, minio_pdf_path, local_pdf_path)

    return f"http://{minio_config['endpoint']}/{BUCKET_NAME}/{minio_pdf_path}"


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

    return f"http://{minio_config['endpoint']}/{BUCKET_NAME}/{minio_pdf_path}"
