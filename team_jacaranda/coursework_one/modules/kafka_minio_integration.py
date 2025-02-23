from kafka import KafkaConsumer
from minio import Minio
import psycopg2
import requests

# Kafka 配置
kafka_bootstrap_servers = 'localhost:9092'
kafka_topic = 'csr-report'

# MinIO 配置
minio_endpoint = 'localhost:9000'
minio_access_key = 'ift_bigdata'
minio_secret_key = 'minio_password'
minio_bucket = 'csr-reports'

# PostgreSQL 配置
pg_host = 'host.docker.internal'
pg_port = 5439
pg_dbname = 'fift'
pg_user = 'postgres'
pg_password = 'postgres'

# 初始化 MinIO 客户端
minio_client = Minio(
    minio_endpoint,
    access_key=minio_access_key,
    secret_key=minio_secret_key,
    secure=False
)

# 初始化 Kafka 消费者
consumer = KafkaConsumer(
    kafka_topic,
    bootstrap_servers=kafka_bootstrap_servers,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='csr-report-group'
)

# 处理 Kafka 消息
for message in consumer:
    # 解析消息
    report_url = message.value.decode('utf-8')
    print(f"Processing report URL: {report_url}")

    # 下载报告文件
    response = requests.get(report_url)
    if response.status_code == 200:
        file_name = report_url.split('/')[-1]
        file_data = response.content

        # 上传到 MinIO
        try:
            minio_client.put_object(
                minio_bucket,
                file_name,
                file_data,
                length=len(file_data),
                content_type='application/pdf'
            )
            print(f"Uploaded {file_name} to MinIO bucket {minio_bucket}")
        except Exception as e:
            print(f"Failed to upload {file_name} to MinIO: {e}")
    else:
        print(f"Failed to download report from {report_url}")
