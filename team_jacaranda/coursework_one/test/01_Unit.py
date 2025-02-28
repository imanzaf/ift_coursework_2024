#!/usr/bin/env python
# coding: utf-8

import pytest
import sys
import os

# 手动添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..', '..')))


# In[ ]:


# test/unit/test_database.py
import pytest
from unittest.mock import Mock, patch
import psycopg2

def test_table_creation():
    """测试表创建逻辑"""
    with patch('psycopg2.connect') as mock_connect:
         # 在此代码块内，所有对 psycopg2.connect 的调用都会被 Mock 对象替代
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn # 定义 connect() 的返回值
        mock_conn.cursor.return_value = mock_cursor
        
        # 执行表创建代码
        from team_jacaranda.coursework_one.modules.create_table import create_table
        create_table()

        # 验证是否调用了正确的SQL
        mock_cursor.execute.assert_called_with("CREATE TABLE IF NOT EXISTS ...")

def test_database_connection():
    """测试数据库连接"""
    with patch('psycopg2.connect') as mock_connect:
        from team_jacaranda.coursework_one.modules.create_table import connect_to_postgres
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
from team_jacaranda.coursework_one.modules.integrate_urls import extract_year

@pytest.mark.parametrize("url,expected", [
    ("https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT _2019.pdf", 2019),
    ("https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ALK_2017.pdf", 2017),
    ("htps:/www.aon.com/getmedia/eae7e9f0-c75f-40de-9061-210510a66a51/Aon-2021-ESG-mpact-Report-Key-Facts-and-Figures.pdf", 2021)
])
def test_extract_year(url, expected):
    assert extract_year(url) == expected


# In[ ]:


# tests/unit/test_kafka_producer.py
from unittest.mock import Mock
from team_jacaranda.coursework_one.modules.kafka_producer import group_reports_by_company

def test_group_reports():
    """测试数据分组逻辑"""
    test_data = [
        ("Alaska Air Group inc", "ALK", "https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ALK_2017.pdf"),
        ("Alaska Air Group inc", "ALK", "https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ALK_2022.pdf"),
        ("Abbott Laboratories", "ABT", "https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT_2019.pdf")
    ]
    grouped = group_reports_by_company(test_data)
    assert grouped == {
        "Alaska Air Group inc": ["https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ALK_2017.pdf", "https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ALK_2022.pdf"],
        "Abbott Laboratories": ["https://www.responsibilityreports.com/HostedData/ResponsibilityReportArchive/a/NYSE_ABT_2019.pdf"]
    }


# In[ ]:





# In[ ]:




