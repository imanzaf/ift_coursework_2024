"""
TODO -
    - Methods for writing and reading pdf object from minio database.
"""

import os
import sys
from datetime import timedelta

from ift_global import MinioFileSystemRepo
from loguru import logger
from minio import Minio
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from config.db import database_settings


class MinioFileSystem(MinioFileSystemRepo, BaseModel):
    """
    Overwrite file read and file write methods in MinioFileSystemRepo to add functionality to process pdf files.

    Useful methods from parent class:
        - list_dir
        - list_files
        - dir_exists
        - file_exists
    """

    bucket_name: str = database_settings.MINIO_BUCKET_NAME
    user: str = database_settings.MINIO_USERNAME
    password: str = database_settings.MINIO_PASSWORD
    endpoint_url: str = f"{database_settings.MINIO_HOST}:{database_settings.MINIO_PORT}"

    @property
    def client(self) -> Minio:
        """
        Initialize Minio Client.
        """
        minio_client = Minio(
            self.endpoint_url,
            access_key=self.user,
            secret_key=self.password,
            secure=False,  # Change to True if using HTTPS
        )
        return minio_client

    def create_bucket(self, bucket_name: str):
        """
        Ensure the bucket exists. Creates it if it doesn't exist.
        """
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def list_files_by_company(self, company_id):
        """
        List all files for a specific company by prefix 'company_id/'.

        :param company_id: The company ID (integer or string).
        :param bucket_name: MinIO bucket name.
        :return: A list of object names belonging to that company's folder.
        """
        prefix = f"{company_id}/"
        objects = self.client.list_objects(
            self.bucket_name, prefix=prefix, recursive=True
        )
        return [obj.object_name for obj in objects]

    def view_pdf(self, object_name: str, expiry_hours=1):
        """
        Generate a presigned URL to view the PDF in a web browser.
        Users can open the link in their browser without explicitly downloading.

        :param object_name: The MinIO path (e.g. "123/2024/report.pdf").
        :param bucket_name: MinIO bucket name.
        :param expiry_hours: The expiry time for the presigned URL.
        :return: A presigned URL string.
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
        """
        Download a file from MinIO to a local path.

        :param file_name: Name of the file in the bucket (same as 'upload_file').
        :param dest_path: Local path to save the file (e.g., "./downloaded.pdf").
        :param bucket_name: MinIO bucket name.
        """
        self.client.fget_object(self.bucket_name, file_name, dest_path)

    def upload_pdf(self, local_file_path: str, company_id: str, report_year: str):
        """
        Writes (uploads) a PDF into a subfolder structure: company_id/year/filename.pdf.

        :param local_file_path: Path to the local PDF file.
        :param company_id: The ID of the company for which the PDF is being uploaded.
        :param report_year: The year of the CSR report.
        :param bucket_name: MinIO bucket name.
        :return: The object name (MinIO path), e.g. "123/2024/report.pdf"
        """
        self.create_bucket(self.bucket_name)

        # Derive a file name from the local file path (e.g., "report.pdf")
        file_name = os.path.basename(local_file_path)
        # Construct the object name with subfolders: e.g. "123/2024/report.pdf"
        object_name = f"{company_id}/{report_year}/{file_name}"

        # upload object
        self.client.fput_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            file_path=local_file_path,
        )

        return object_name

    def write_pdf_bytes(
        self, pdf_bytes: bytes, company_id: str, report_year: str, file_name: str
    ):
        """
        Writes (uploads) a PDF into a subfolder structure: company_id/year/filename.pdf.

        :param pdf_bytes: The PDF file as bytes.
        :param company_id: The ID of the company for which the PDF is being uploaded.
        :param report_year: The year of the CSR report.
        :return: The object name (MinIO path), e.g. "123/2024/report.pdf"
        """
        self.create_bucket(self.bucket_name)

        # Construct the object name with subfolders: e.g. "123/2024/report.pdf"
        object_name = f"{company_id}/{report_year}/{file_name}"
        # upload object
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=pdf_bytes,
            length=len(pdf_bytes),
        )

        return object_name


if __name__ == "__main__":
    minio = MinioFileSystem()
