import os
import sys
from datetime import timedelta

from ift_global import MinioFileSystemRepo
from loguru import logger
from minio import Minio

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from config.db import database_settings


class MinioFileSystem(MinioFileSystemRepo):
    """Overwrite file read and file write methods in MinioFileSystemRepo to add functionality to process PDF files.

    Attributes:
        bucket_name (str): The name of the MinIO bucket.
        user (str): The username for MinIO.
        password (str): The password for MinIO.
        endpoint_url (str): The endpoint URL used to connect to MinIO, consisting of the MinIO host address and port.
    """

    def __init__(self):
        self.bucket_name = database_settings.MINIO_BUCKET_NAME
        self.client = Minio(
            f"{database_settings.MINIO_HOST}:{database_settings.MINIO_PORT}",
            access_key=database_settings.MINIO_USERNAME,
            secret_key=database_settings.MINIO_PASSWORD,
            secure=False,  # Change to True if using HTTPS
        )

    def create_bucket(self, bucket_name: str):
        """Ensures the bucket exists. Creates it if it doesn't exist.

        Args:
            bucket_name (str): The name of the MinIO bucket.

        Example:
            >>> minio = MinioFileSystem()
            >>> minio.create_bucket("my-bucket")
            # Creates a bucket named "my-bucket" if it doesn't exist.
        """
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def list_files_by_company(self, company_id):
        """Lists all files for a specific company by prefix 'company_id/'.

        Args:
            company_id (str or int): The company ID.

        Returns:
            list: A list of object names belonging to that company's folder.
        """
        prefix = f"{company_id}/"
        objects = self.client.list_objects(
            self.bucket_name, prefix=prefix, recursive=True
        )
        return [obj.object_name for obj in objects]

    def view_pdf(self, object_name: str, expiry_hours: int = 1):
        """Generates a presigned URL to view the PDF in a web browser.

        Users can open the link in their browser without explicitly downloading.

        Args:
            object_name (str): The MinIO path (e.g., "123/2024/report.pdf").
            expiry_hours (int, optional): The expiry time for the presigned URL in hours. Defaults to 1.

        Returns:
            str: A presigned URL string. Returns None if an error occurs.
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name, object_name, expires=timedelta(hours=expiry_hours)
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def download_file(self, file_name: str, dest_path: str):
        """Downloads a file from MinIO to a local path.

        Args:
            file_name (str): The name of the file in the bucket.
            dest_path (str): The local path to save the file (e.g., "./downloaded.pdf").
        """
        self.client.fget_object(self.bucket_name, file_name, dest_path)

    def upload_pdf(self, local_file_path: str, company_id: str, report_year: str):
        """Uploads a PDF into a subfolder structure: company_id/year/filename.pdf.

        Args:
            local_file_path (str): The path to the local PDF file.
            company_id (str): The ID of the company for which the PDF is being uploaded.
            report_year (str): The year of the CSR report.

        Returns:
            str: The object name (MinIO path), e.g., "123/2024/report.pdf".
        """
        self.create_bucket(self.bucket_name)

        # Derive a file name from the local file path (e.g., "report.pdf")
        file_name = os.path.basename(local_file_path)
        # Construct the object name with subfolders: e.g., "123/2024/report.pdf"
        object_name = f"{company_id}/{report_year}/{file_name}"

        # Upload object
        self.client.fput_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            file_path=local_file_path,
        )

        return object_name

    def write_pdf_bytes(
        self,
        pdf_bytes: bytes,
        file_size: int,
        company_id: str,
        report_year: str,
        file_name: str,
    ):
        """Uploads a PDF (as bytes) into a subfolder structure: company_id/year/filename.pdf.

        Args:
            pdf_bytes (bytes): The PDF file as bytes.
            company_id (str): The ID of the company for which the PDF is being uploaded.
            report_year (str): The year of the CSR report.
            file_name (str): The name of the file to be saved.

        Returns:
            str: The object name (MinIO path), e.g., "123/2024/report.pdf".
        """
        self.create_bucket(self.bucket_name)

        # Construct the object name with subfolders: e.g., "123/2024/report.pdf"
        object_name = f"{company_id}/{report_year}/{file_name}"
        # Upload object
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=pdf_bytes,
            length=file_size,
        )

        return object_name


if __name__ == "__main__":
    minio = MinioFileSystem()
