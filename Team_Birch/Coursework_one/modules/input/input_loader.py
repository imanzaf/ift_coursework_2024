from minio import Minio
import os
from werkzeug.utils import secure_filename
from ..db.db_connection import load_config
import uuid

# get config from minio config
config = load_config()
minio_client = Minio(
    config['minio']['host'],
    access_key=config['minio']['access_key'],
    secret_key=config['minio']['secret_key'],
    secure=False
)

def upload_files_to_minio(files, company_name, report_date):
    """
    Uploads a batch of files to MinIO and returns the URL of each file.
    :param files: list of uploaded files
    :param company_name: company name
    :param report_date: report date
    :return: list of file URLs
    """
    uploaded_files_urls = []
    bucket_name = config['minio']['bucket_name']

    # check bucket
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    # Define the relative path for temporary storage
    temp_dir = os.path.join(os.getcwd(), 'temp_uploads')  # Relative path to current working directory
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for file in files:
        # Generate a relative path for the file in temp_uploads
        file_name = f"{company_name}/{report_date}/{uuid.uuid4().hex}_report.pdf"  # Unique file name with relative path
        file_name = secure_filename(file_name)  # Ensure the filename is safe

        # Save the file to the relative temp path
        temp_file_path = os.path.join(temp_dir, file_name)
        file.save(temp_file_path)

        # Upload to MinIO
        minio_client.fput_object(bucket_name, file_name, temp_file_path)
        os.remove(temp_file_path)

        # Return the URL
        file_url = f"http://{config['minio']['host']}/{bucket_name}/{file_name}"
        uploaded_files_urls.append(file_url)

    return uploaded_files_urls
