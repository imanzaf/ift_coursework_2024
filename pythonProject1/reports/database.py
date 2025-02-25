# database_manager.py
import psycopg2
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class PostgresManager:
    def __init__(self, host="localhost", port="5432", user="postgres", password="postgres", dbname="postgres"):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=dbname
        )
        self.cur = self.conn.cursor()
        # 如果需要创建表:
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS pdf_records (
                id SERIAL PRIMARY KEY,
                company VARCHAR(255),
                url TEXT,
                year INT,
                file_hash VARCHAR(64) UNIQUE,
                filename TEXT UNIQUE, -- filename 字段，UNIQUE 避免重复
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        self.conn.commit()
        
    def check_pdf_record(self, file_hash: str) -> bool:
        query = "SELECT COUNT(*) FROM pdf_records WHERE file_hash = %s;"
        self.cur.execute(query, (file_hash,))
        count = self.cur.fetchone()[0]
        return count > 0  # 如果 count > 0，说明已存在
    
    def insert_pdf_record(self, record: Dict):
        query = "SELECT COUNT(*) FROM pdf_records WHERE file_hash = %s;"
        self.cur.execute(query, (record['file_hash'],))
        count = self.cur.fetchone()[0]

        if count == 0:  # 只有当文件不存在时才插入
            self.cur.execute("""
            INSERT INTO pdf_records (company, url, year, file_hash, filename)
            VALUES (%s, %s, %s, %s, %s);
        """, (record['company'], record['url'], record['year'], record['file_hash'], record['filename']))
            self.conn.commit()
            logger.info(f"[Postgres] Inserted record for {record['company']} - {record['year']}")
        else:
            logger.info(f"[Postgres] Skipped {record['filename']}, already exists.")
   
    def close(self):
        self.cur.close()
        self.conn.close()
    