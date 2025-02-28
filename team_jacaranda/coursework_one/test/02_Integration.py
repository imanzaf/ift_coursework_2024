#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# tests/integration/test_minio_postgres.py
import pytest
from unittest.mock import Mock, patch
from minio.error import S3Error

def test_minio_upload_integration():
    """测试MinIO上传与数据库记录集成"""
    with patch('team_jacaranda.coursework_one.modules.minio_client') as mock_minio, \
         patch('team_jacaranda.coursework_one.modules.psycopg2.connect') as mock_db:
        
        # 配置Mock
        mock_db.return_value.cursor.return_value.fetchone.return_value = ("TEST", 2023)
        mock_minio.put_object.return_value = True
        
        # 执行上传逻辑
        from team_jacaranda.coursework_one.modules.kafka_minio_integration import upload_to_minio
        upload_to_minio("test.pdf", b"content")
        
        # 验证MinIO调用
        mock_minio.put_object.assert_called_once()
        
        # 验证数据库更新
        mock_db.return_value.cursor.return_value.execute.assert_called_with(
            "UPDATE ... SET minio_path = %s WHERE report_url = %s",
            ("test.pdf", "http://test.url")
        )


# In[ ]:


# tests/integration/test_kafka_ingestion.py
from kafka import KafkaConsumer
from unittest.mock import Mock, patch

def test_kafka_consumer_integration():
    """测试Kafka消费与处理集成"""
    with patch('team_jacaranda.coursework_one.modules.KafkaConsumer') as mock_consumer, \
         patch('team_jacaranda.coursework_one.modules.kafka_minio_integration.download_pdf') as mock_download:
        
        # 配置模拟消息
        mock_consumer_instance = Mock()
        mock_consumer_instance.__iter__.return_value = [Mock(value={
            'company_name': 'Abbott Laboratories',
            'report_urls': ['https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT _2019.pdf']
        })]
        mock_consumer.return_value = mock_consumer_instance
        
        # 执行消费逻辑
        from your_module import main
        main()
        
        # 验证下载和上传操作
        mock_download.assert_called_once_with("https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT _2019.pdf")


# In[ ]:




