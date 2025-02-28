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
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS pdf_records (
                id SERIAL PRIMARY KEY,
                company VARCHAR(255),
                url TEXT,
                year INT,
                file_hash VARCHAR(64) UNIQUE,
                filename TEXT UNIQUE, 
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT unique_company_year UNIQUE (company, year)
            );
        """)
        self.conn.commit()
        
    def check_pdf_record(self, file_hash: str) -> bool:
        query = "SELECT COUNT(*) FROM pdf_records WHERE file_hash = %s;"
        self.cur.execute(query, (file_hash,))
        count = self.cur.fetchone()[0]
        return count > 0  # if count > 0，it already exists
    
    def insert_pdf_record(self, record: Dict):
    # Check if database already exists (company, year)
        query = "SELECT 1 FROM pdf_records WHERE company = %s AND year = %s;"
        self.cur.execute(query, (record['company'], record['year']))
        exists = self.cur.fetchone()

        if exists:  # Skip if records already exist for that company for that year
            logger.info(f"[Postgres] Skipping {record['company']} {record['year']}, already exists.")
            return
    
    # insert data
        try:
            self.cur.execute("""
            INSERT INTO pdf_records (company, url, year, file_hash, filename)
            VALUES (%s, %s, %s, %s, %s);
            """, (record['company'], record['url'], record['year'], record['file_hash'], record['filename']))
            self.conn.commit()
            logger.info(f"[Postgres] Inserted record for {record['company']} - {record['year']}")
        except Exception as e:
            self.conn.rollback()  
            logger.error(f"[Postgres] Insert failed: {str(e)}")

   
    def close(self):
        self.cur.close()
        self.conn.close()
    