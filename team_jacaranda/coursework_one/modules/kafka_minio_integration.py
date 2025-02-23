import io
import json
import requests
from kafka import KafkaConsumer
from minio import Minio
from minio.error import S3Error
import psycopg2

# Kafka 配置
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'csr-report'

# MinIO 配置
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'ift_bigdata'
MINIO_SECRET_KEY = 'minio_password'
MINIO_BUCKET = 'csr-reports'

# PostgreSQL 配置
PG_HOST = 'host.docker.internal'
PG_PORT = 5439
PG_DB = 'fift'
PG_USER = 'postgres'
PG_PASSWORD = 'postgres'

# 初始化 MinIO 客户端
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # 如果使用 HTTPS，设置为 True
)

# 初始化 Kafka 消费者
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# 连接到 PostgreSQL
def connect_to_postgres():
    print("Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        print("Successfully connected to PostgreSQL!")
        return conn
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        raise

# 下载 PDF 文件
def download_pdf(url):
    print(f"Downloading PDF from {url}...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Successfully downloaded PDF from {url}")
            return response.content
        else:
            raise Exception(f"Failed to download PDF from {url}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading PDF from {url}: {e}")
        raise

# 上传 PDF 文件到 MinIO
def upload_to_minio(file_name, file_data):
    print(f"Uploading {file_name} to MinIO...")
    try:
        # 调试信息：打印 file_data 的类型和长度
        print(f"File data type: {type(file_data)}")
        print(f"File data length: {len(file_data)}")

        # 将 bytes 对象转换为 BytesIO 对象
        file_stream = io.BytesIO(file_data)

        # 上传文件到 MinIO
        minio_client.put_object(
            MINIO_BUCKET,
            file_name,
            file_stream,  # 使用文件流对象
            length=len(file_data),
            content_type='application/pdf'
        )
        print(f"Successfully uploaded {file_name} to MinIO bucket {MINIO_BUCKET}")
    except S3Error as e:
        print(f"Failed to upload {file_name} to MinIO: {e}")
        raise

# 主逻辑
def main():
    print("Starting Kafka-MinIO integration script...")
    conn = connect_to_postgres()
    cursor = conn.cursor()

    print(f"Listening for messages on Kafka topic '{KAFKA_TOPIC}'...")
    for message in consumer:
        print("\n--- Processing new message ---")
        data = message.value
        company_name = data['company_name']
        report_urls = data['report_urls']

        print(f"Processing company: {company_name}")
        print(f"Found {len(report_urls)} report URLs")

        for url in report_urls:
            try:
                print(f"\nProcessing URL: {url}")

                # 下载 PDF 文件
                pdf_data = download_pdf(url)

                # 生成文件名
                file_name = f"{company_name}_{url.split('/')[-1]}"
                print(f"Generated file name: {file_name}")

                # 上传到 MinIO
                upload_to_minio(file_name, pdf_data)

                # 记录上传状态到 PostgreSQL
                print(f"Recording upload status in PostgreSQL for {file_name}...")
                cursor.execute(
                    "INSERT INTO csr_reporting.company_reports (company_name, report_url, minio_path) VALUES (%s, %s, %s)",
                    (company_name, url, file_name)
                )
                conn.commit()
                print(f"Successfully recorded {file_name} in PostgreSQL")
            except Exception as e:
                print(f"Error processing {url}: {e}")

    cursor.close()
    conn.close()
    print("Script finished.")

if __name__ == "__main__":
    main()
