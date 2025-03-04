#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# tests/integration/test_minio_postgres.py
import pytest
from unittest.mock import Mock, patch
from minio.error import S3Error

def test_minio_upload_integration():
    """Test MinIO upload and database record integration"""
    with patch('team_jacaranda.coursework_one.modules.minio_client') as mock_minio, \
         patch('team_jacaranda.coursework_one.modules.psycopg2.connect') as mock_db:
        
        # Configure Mock
        mock_db.return_value.cursor.return_value.fetchone.return_value = ("TEST", 2023)
        mock_minio.put_object.return_value = True
        
        # Execute upload logic
        from team_jacaranda.coursework_one.modules.kafka_minio_integration import upload_to_minio
        upload_to_minio("test.pdf", b"content")
        
        # Verify MinIO call
        mock_minio.put_object.assert_called_once()
        
        # Verify database update
        mock_db.return_value.cursor.return_value.execute.assert_called_with(
            "UPDATE ... SET minio_path = %s WHERE report_url = %s",
            ("test.pdf", "http://test.url")
        )


# In[ ]:


# tests/integration/test_kafka_ingestion.py
from kafka import KafkaConsumer
from unittest.mock import Mock, patch

def test_kafka_consumer_integration():
    """Test Kafka consumption and processing integration"""
    with patch('team_jacaranda.coursework_one.modules.KafkaConsumer') as mock_consumer, \
         patch('team_jacaranda.coursework_one.modules.kafka_minio_integration.download_pdf') as mock_download:
        
        # Configure mock message
        mock_consumer_instance = Mock()
        mock_consumer_instance.__iter__.return_value = [Mock(value={
            'company_name': 'Abbott Laboratories',
            'report_urls': ['https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT _2019.pdf']
        })]
        mock_consumer.return_value = mock_consumer_instance
        
        # Execute consumption logic
        from your_module import main
        main()
        
        # Verify download and upload operations
        mock_download.assert_called_once_with("https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT _2019.pdf")


# In[ ]:
