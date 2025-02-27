from minio import Minio
from minio.error import S3Error

def main():
    company = input("Enter company name: ").strip()
    year = input("Enter year: ").strip()
    client = Minio(
        "localhost:9000",
        access_key="ift_bigdata",
        secret_key="minio_password",
        secure=False
    )
    bucket_name = "csr-reports"
    object_name = f"{company}_{year}.pdf"
    download_path = f"./{object_name}"
    try:
        client.fget_object(bucket_name, object_name, download_path)
        print(f"Successfully downloaded file: {download_path}")
    except S3Error as e:
        print(f"Download failed, error info: {e}")

if __name__ == '__main__':
    main()
