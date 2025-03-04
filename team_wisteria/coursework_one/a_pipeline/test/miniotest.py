import pytest
import boto3
from minio import Minio
from io import BytesIO
from unittest.mock import patch

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "ift_bigdata"
MINIO_SECRET_KEY = "minio_password"
BUCKET_NAME = "test-bucket"

@pytest.fixture(scope="module")
def minio_client():
    """
    Creating a MinIO client and creating a test bucket
    """
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
    
    yield client  

    objects = client.list_objects(BUCKET_NAME, recursive=True)
    for obj in objects:
        client.remove_object(BUCKET_NAME, obj.object_name)
    client.remove_bucket(BUCKET_NAME)

def test_minio_upload(minio_client):

    file_data = b"Hello, MinIO!"
    file_name = "test_file.txt"

    minio_client.put_object(
        BUCKET_NAME,
        file_name,
        BytesIO(file_data),
        length=len(file_data),
        content_type="text/plain"
    )

    objects = list(minio_client.list_objects(BUCKET_NAME))
    assert any(obj.object_name == file_name for obj in objects), "File not successfully uploaded to MinIO"

def test_minio_download(minio_client):

    file_name = "test_file.txt"
    response = minio_client.get_object(BUCKET_NAME, file_name)
    content = response.read()

    assert content == b"Hello, MinIO!", "MinIO Downloaded file content does not match what was uploaded"

def test_minio_delete(minio_client):

    file_name = "test_file.txt"
    minio_client.remove_object(BUCKET_NAME, file_name)

    objects = list(minio_client.list_objects(BUCKET_NAME))
    assert not any(obj.object_name == file_name for obj in objects), "File not successfully deleted"
