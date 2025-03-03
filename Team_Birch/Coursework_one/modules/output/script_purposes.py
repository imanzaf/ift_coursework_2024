from minio import Minio
from minio.error import S3Error

def init_minio_client():
    client = Minio(
        "8.134.166.116:9000",
        access_key="ift_bigdata",
        secret_key="minio_password",
        secure=False
    )
    return client

def upload_file_to_minio(file, company_name, report_date):
    minio_client = init_minio_client()
    file_name = f"{company_name}_{report_date}_report.pdf"
    bucket_name = "reports"

    try:
        # check bucket
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # push files
        minio_client.put_object(
            bucket_name, file_name, file, len(file.read())
        )

        # get presigned URL
        file_url = minio_client.presigned_get_object(bucket_name, file_name)
        return file_url
    except S3Error as e:
        raise e
