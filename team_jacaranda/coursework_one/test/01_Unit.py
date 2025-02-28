#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# tests/unit/test_database.py
import pytest
from unittest.mock import Mock, patch
import psycopg2
import sys
import os

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 获取上级目录，即 modules 文件夹所在的目录
modules_dir = os.path.abspath(os.path.join(current_dir, '..', 'modules'))

# 将 modules 文件夹添加到 sys.path 中
sys.path.append(modules_dir)

def test_table_creation():
    """测试表创建逻辑"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 执行表创建代码
        from create_table import create_table
        create_table()
        
        mock_cursor.execute.assert_called_with("CREATE TABLE IF NOT EXISTS ...")

def test_database_connection():
    """测试数据库连接"""
    with patch('psycopg2.connect') as mock_connect:
        from kafka__minio_integration import connect_to_postgres
        connect_to_postgres()
        mock_connect.assert_called_once_with(
            host="host.docker.internal",
            port=5439,
            dbname="fift",
            user="postgres",
            password="postgres"
        )


# In[ ]:


# tests/unit/test_url_processing.py
import pytest
from integrate_urls import extract_year  # 替换为实际模块

@pytest.mark.parametrize("url,expected", [
    ("https://reports/2023.pdf", 2023),
    ("https://reports_2024_annual.pdf", 2024),
    ("https://invalid/url", None)
])
def test_extract_year(url, expected):
    assert extract_year(url) == expected


# In[ ]:


# tests/unit/test_kafka_producer.py
from unittest.mock import Mock
from kafka_producer import group_reports_by_company  # 替换为实际模块

def test_group_reports():
    """测试数据分组逻辑"""
    test_data = [
        ("CompanyA", "A", "url1"),
        ("CompanyA", "A", "url2"),
        ("CompanyB", "B", "url3")
    ]
    grouped = group_reports_by_company(test_data)
    assert grouped == {
        "CompanyA": ["url1", "url2"],
        "CompanyB": ["url3"]
    }


# In[ ]:





# In[ ]:




