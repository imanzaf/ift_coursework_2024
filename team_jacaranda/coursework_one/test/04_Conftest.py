#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# tests/conftest.py
import pytest
import psycopg2
from minio import Minio
from kafka import KafkaProducer, KafkaConsumer
import os
import time
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# --------------------------
# 全局配置参数
# --------------------------
POSTGRES_TEST_CONFIG = {
    "host": "localhost" if os.getenv("DOCKER_ENV") else "host.docker.internal",
    "port": 5439,
    "dbname": "fift_test",  # 测试专用数据库
    "user": "postgres",
    "password": "postgres"
}

MINIO_TEST_CONFIG = {
    "endpoint": "localhost:9000",
    "access_key": "ift_bigdata",
    "secret_key": "minio_password",
    "secure": False,
    "bucket": "csreport-test"  # 测试专用桶
}

KAFKA_TEST_CONFIG = {
    "bootstrap_servers": "localhost:9092",
    "topic": "csr-report-test"
}

# --------------------------
# 数据库 Fixtures
# --------------------------
@pytest.fixture(scope="session")
def postgres_conn():
    """全局PostgreSQL连接（测试会话级别）"""
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**POSTGRES_TEST_CONFIG)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("Successfully connected to PostgreSQL")
            yield conn
            break
        except psycopg2.OperationalError as e:
            if i == max_retries - 1:
                raise RuntimeError(f"Failed to connect to PostgreSQL after {max_retries} attempts: {e}")
            print(f"PostgreSQL connection failed, retrying... ({i+1}/{max_retries})")
            time.sleep(2)
    
    # 测试后清理
    with conn.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS csr_reporting.company_reports CASCADE")
        cursor.execute("DROP TABLE IF EXISTS csr_reporting.company_static CASCADE")
    conn.close()

@pytest.fixture(scope="function")
def db_setup(postgres_conn):
    """每个测试用例前的数据库初始化"""
    with postgres_conn.cursor() as cursor:
        # 创建测试表结构
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS csr_reporting.company_static (
                security TEXT PRIMARY KEY,
                company_name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS csr_reporting.company_reports (
                id SERIAL PRIMARY KEY,
                security TEXT REFERENCES csr_reporting.company_static(security),
                report_url VARCHAR(255),
                report_year INTEGER,
                minio_path VARCHAR(255)
            )
        """)
        # 插入基础测试数据
        cursor.execute("""
            INSERT INTO csr_reporting.company_static (security, company_name)
            VALUES 
                ('ALK', 'Alaska Air Group inc'),
                ('ABT', 'Abbott Laboratories')
            ON CONFLICT DO NOTHING
        """)
    yield
    # 测试后清理数据（保留表结构）
    with postgres_conn.cursor() as cursor:
        cursor.execute("TRUNCATE csr_reporting.company_reports CASCADE")

# --------------------------
# MinIO Fixtures
# --------------------------
@pytest.fixture(scope="session")
def minio_client():
    """全局MinIO客户端"""
    client = Minio(
        MINIO_TEST_CONFIG["endpoint"],
        access_key=MINIO_TEST_CONFIG["access_key"],
        secret_key=MINIO_TEST_CONFIG["secret_key"],
        secure=MINIO_TEST_CONFIG["secure"]
    )
    
    # 确保测试桶存在
    if not client.bucket_exists(MINIO_TEST_CONFIG["bucket"]):
        client.make_bucket(MINIO_TEST_CONFIG["bucket"])
    
    yield client
    
    # 测试后清理所有测试文件
    objects = client.list_objects(MINIO_TEST_CONFIG["bucket"], recursive=True)
    for obj in objects:
        client.remove_object(MINIO_TEST_CONFIG["bucket"], obj.object_name)

# --------------------------
# Kafka Fixtures
# --------------------------
@pytest.fixture(scope="session")
def kafka_producer():
    """Kafka生产者（会话级别）"""
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_TEST_CONFIG["bootstrap_servers"],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    yield producer
    producer.close()

@pytest.fixture(scope="function")
def kafka_consumer():
    """Kafka消费者（函数级别）"""
    consumer = KafkaConsumer(
        KAFKA_TEST_CONFIG["topic"],
        bootstrap_servers=KAFKA_TEST_CONFIG["bootstrap_servers"],
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        consumer_timeout_ms=5000
    )
    yield consumer
    consumer.close()

# --------------------------
# 其他工具函数
# --------------------------
@pytest.fixture(scope="session", autouse=True)
def check_services_available():
    """全局服务可用性检查"""
    required_services = {
        "PostgreSQL": (POSTGRES_TEST_CONFIG["host"], POSTGRES_TEST_CONFIG["port"]),
        "MinIO": (MINIO_TEST_CONFIG["endpoint"].split(":")[0], int(MINIO_TEST_CONFIG["endpoint"].split(":")[1])),
        "Kafka": (KAFKA_TEST_CONFIG["bootstrap_servers"].split(":")[0], 9092)
    }
    
    for service, (host, port) in required_services.items():
        attempt = 0
        max_attempts = 5
        while attempt < max_attempts:
            try:
                with socket.create_connection((host, port), timeout=1):
                    print(f"{service} service is available")
                    break
            except (socket.timeout, ConnectionRefusedError) as e:
                attempt += 1
                if attempt == max_attempts:
                    raise RuntimeError(f"{service} service not available at {host}:{port}")
                print(f"Waiting for {service} service... (attempt {attempt}/{max_attempts})")
                time

