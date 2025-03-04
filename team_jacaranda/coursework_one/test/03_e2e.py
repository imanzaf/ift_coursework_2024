#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# tests/e2e/test_data_pipeline.py
import pytest
from kafka import KafkaProducer, KafkaConsumer
from minio import Minio
import psycopg2
import time

@pytest.mark.e2e
def test_full_pipeline():
    """End-to-end data flow test: Producer → Kafka → Consumer → MinIO/DB"""
    
    # 1. Producer sends data
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    producer.send('csr-report', value={
        'company_name': 'Abbott Laboratories',
        'report_urls': ['https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT _2019.pdf']
    })
    producer.flush()
    
    # 2. Consumer processing (wait for 10 seconds)
    time.sleep(10)
    
    # 3. Verify MinIO
    minio_client = Minio(
        "localhost:9000",
        access_key="ift_bigdata",
        secret_key="minio_password",
        secure=False
    )
    assert minio_client.stat_object("csreport", "Abbott Laboratories_2019.pdf")
    
    # 4. Verify database
    conn = psycopg2.connect(
        host="host.docker.internal",
        port=5439,
        dbname="fift",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT minio_path FROM company_reports WHERE report_url = 'https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT _2019.pdf'")
    assert cursor.fetchone()[0] == "Abbott Laboratories_2019.pdf"

# In[ ]:
