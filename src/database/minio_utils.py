"""
minio_utils.py

This module provides a MinioFileSystem class that extends the MinioFileSystemRepo
class from ift_global. It leverages Pydantic for environment-based defaults and
the official minio Python SDK for direct data-lake interactions.


Created: 2025-02-26

Usage:
    # Typical usage inside 'test_minio.py':
    from src.database.minio_utils import MinioFileSystem

    minio_fs = MinioFileSystem()
    minio_fs.create_bucket("my-bucket")
    ...
"""

import os
import sys
from datetime import timedelta

from ift_global import MinioFileSystemRepo
from loguru import logger
from minio import Minio
from pydantic import BaseModel

# Ensure we can find config/ and other modules in the parent directories.
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from config.db import database_settings


class MinioFileSystem(MinioFileSystemRepo, BaseModel):
    """
    MinioFileSystem extends MinioFileSystemRepo from ift_global, incorporating
    environment-based defaults (via Pydantic) and custom PDF-file handling
    methods. This class is responsible for high-level MinIO operations within
    the data-lake architecture.

    Fields:
        bucket_name (str):
            The default bucket name used for all operations. Pulled from
            database_settings.MINIO_BUCKET_NAME.
        user (str):
            MinIO user access key. e.g., 'admin'
        password (str):
            MinIO user secret key. e.g., 'adminpassword'
        endpoint_url (str):
            Full MinIO endpoint including protocol (e.g., "http://localhost:9000").

    Implementation Notes:
    - We rely on the parent 'MinioFileSystemRepo' from ift_global for the
      base functionalities and Boto-based bridging.
    - This class overrides/extends certain behaviors, especially for
      PDF-specific or file-based workflows.
    - The 'client' property uses the official 'minio' PyPI package to handle
      direct S3-compatible calls.

    Example:
        >>> from src.database.minio_utils import MinioFileSystem
        >>> minio_fs = MinioFileSystem()
        >>> minio_fs.create_bucket("csr-reports")
        >>> obj_name = minio_fs.upload_pdf("local_report.pdf", "123", "2024")
        >>> presigned_url = minio_fs.view_pdf(obj_name, expiry_hours=2)
        >>> print(presigned_url)


    """

    bucket_name: str = database_settings.MINIO_BUCKET_NAME
    user: str = database_settings.MINIO_USERNAME
    password: str = database_settings.MINIO_PASSWORD
    # Must include http:// or https:// for Boto-based usage in ift_global
    endpoint_url: str = f"http://{database_settings.MINIO_HOST}:{database_settings.MINIO_PORT}"

    def __init__(self, **kwargs):
        """
        Custom constructor:
          1) Initializes pydantic fields from environment variables or defaults.
          2) Calls the ift_global MinioFileSystemRepo constructor with these fields.
          3) Ensures 'endpoint_url' is valid to avoid Boto 'Invalid endpoint' errors.

        Parameters:
            kwargs: Optional overrides if the user wants to pass custom values
                    instead of environment defaults.

        Example:
            >>> minio_fs = MinioFileSystem(
            ...     bucket_name="csr-reports-dev",
            ...     user="devuser",
            ...     password="devpass",
            ...     endpoint_url="http://devminio:9000"
            ... )
        """
        # 1) Pydantic initialization for local fields
        BaseModel.__init__(self, **kwargs)

        # 2) Call parent constructor from ift_global, passing required fields
        MinioFileSystemRepo.__init__(
            self,
            bucket_name=self.bucket_name,
            user=self.user,
            password=self.password,
            endpoint_url=self.endpoint_url,
        )

    @property
    def client(self) -> Minio:
        """
        Returns a Minio client (official minio PyPI package) for direct
        S3-compatible calls. Removes 'http://' for the host:port usage expected
        by minio-py when secure=False.

        Returns:
            Minio: An instance of the official Minio SDK client.

        Implementation Detail:
        - We do 'self.endpoint_url.replace("http://", "")' because minio-py
          typically wants just 'host:port' if 'secure=False'.
        - If using HTTPS, you’d set 'secure=True' and ensure 'endpoint_url' has https://.

        Example:
            >>> cli = self.client
            >>> print(cli.list_buckets())
        """
        return Minio(
            self.endpoint_url.replace("http://", ""),
            access_key=self.user,
            secret_key=self.password,
            secure=False
        )

    def create_bucket(self, bucket_name: str):
        """
        Ensures the specified bucket exists on MinIO. If it doesn’t exist,
        this method creates it.

        Args:
            bucket_name (str): Name of the bucket to create if not present.

        Returns:
            None
        """
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def list_files_by_company(self, company_id: str):
        """
        Lists all files associated with a given company ID prefix. 
        The structure is assumed to be 'company_id/year/file.pdf'.

        Args:
            company_id (str): The company ID or unique prefix in the bucket.

        Returns:
            List[str]: A list of object names (file paths) matching that prefix.
        """
        prefix = f"{company_id}/"
        objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]

    def view_pdf(self, object_name: str, expiry_hours: int = 1) -> str:
        """
        Generates a presigned URL to view a PDF in the browser without
        explicitly downloading it.

        Args:
            object_name (str): Path to the MinIO object (e.g., "123/2024/report.pdf").
            expiry_hours (int): Number of hours before the URL expires.

        Returns:
            str: A presigned URL if successful, or None on error.
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(hours=expiry_hours)
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def download_file(self, file_name: str, dest_path: str):
        """
        Downloads an object from MinIO to a local file path.

        Args:
            file_name (str): The object name in MinIO (e.g., '123/2024/report.pdf').
            dest_path (str): Local file path to write the downloaded file.
        """
        self.client.fget_object(self.bucket_name, file_name, dest_path)

    def upload_pdf(self, local_file_path: str, company_id: str, report_year: str) -> str:
        """
        Uploads a local PDF file to MinIO under 'company_id/year/file.pdf'.

        Args:
            local_file_path (str): Path to the local PDF.
            company_id (str): The company identifier or prefix.
            report_year (str): The CSR report year.

        Returns:
            str: The object name (MinIO path), e.g., '123/2024/report.pdf'.
        """
        self.create_bucket(self.bucket_name)
        file_name = os.path.basename(local_file_path)
        object_name = f"{company_id}/{report_year}/{file_name}"
        self.client.fput_object(self.bucket_name, object_name, local_file_path)
        return object_name

    def write_pdf_bytes(self, pdf_bytes: bytes, company_id: str, report_year: str, file_name: str) -> str:
        """
        Writes an in-memory PDF (bytes) to MinIO, avoiding local disk usage.
        The final path is 'company_id/year/file.pdf'.

        Args:
            pdf_bytes (bytes): The PDF data in memory.
            company_id (str): The company identifier or prefix.
            report_year (str): The CSR report year.
            file_name (str): Filename (e.g., 'report.pdf').

        Returns:
            str: The object path in MinIO.
        """
        self.create_bucket(self.bucket_name)
        object_name = f"{company_id}/{report_year}/{file_name}"
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=pdf_bytes,
            length=len(pdf_bytes),
        )
        return object_name


if __name__ == "__main__":
    # Minimal local test to ensure instantiation and logging
    fs = MinioFileSystem()
    logger.info(
        f"Instantiated MinioFileSystem with endpoint='{fs.endpoint_url}' "
        f"and bucket='{fs.bucket_name}'."
    )
