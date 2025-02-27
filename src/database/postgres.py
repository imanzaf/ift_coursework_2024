"""
Methods for interacting with postgres database, focusing on:
- reading from csr_reporting.company_static
- writing to csr_reporting.company_csr_reports
"""

import os
import sys
import psycopg2
from loguru import logger
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from sqlalchemy import create_engine, engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from config.db import database_settings


class PostgreSQLDB(BaseModel):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def connection(self):
        engine = self._conn_postgres_psycopg2()
        return engine

    def close(self, commit=True):
        if commit:
            self.connection.commit()
        self.connection.close()

    def execute(self, query, params=None):
        if self.connection is None:
            logger.error(f"No connection to {database_settings.POSTGRES_DB_NAME}.")
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            cursor.close()
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")

    def fetch(self, query, params=None):
        if self.connection is None:
            logger.error(f"No connection to {database_settings.POSTGRES_DB_NAME}.")
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return []

    #
    # For storing final URLs
    #
    def store_csr_report(self, symbol, report_url, report_year):
        """
        Insert a new CSR report record into the table:
          csr_reporting.company_csr_reports
        If (symbol, report_year) is unique, we skip duplicates.
        """
        query = """
        INSERT INTO csr_reporting.company_csr_reports (symbol, report_url, report_year, retrieved_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (symbol, report_year) DO NOTHING
        """
        self.execute(query, (symbol, report_url, report_year))

    def get_csr_reports_by_symbol(self, symbol):
        """
        Retrieve all CSR reports for a specific symbol, ordered by year desc.
        """
        query = """
        SELECT symbol, report_url, report_year, retrieved_at
        FROM csr_reporting.company_csr_reports
        WHERE symbol = %s
        ORDER BY report_year DESC
        """
        return self.fetch(query, (symbol,))

    #
    # Helpers to read from company_static
    #
    def fetch_all_companies(self):
        """
        Returns a list of (symbol, security, gics_sector, gics_industry, country, region).
        """
        query = """
        SELECT symbol, security, gics_sector, gics_industry, country, region
        FROM csr_reporting.company_static
        """
        return self.fetch(query)

    @staticmethod
    def _conn_postgres_sqlalchemy():
        url_object = engine.URL.create(
            drivername=database_settings.POSTGRES_DRIVER,
            username=database_settings.POSTGRES_USERNAME,
            password=database_settings.POSTGRES_PASSWORD,
            host=database_settings.POSTGRES_HOST,
            database=database_settings.POSTGRES_DB_NAME,
            port=database_settings.POSTGRES_PORT,
        )
        try:
            connection_engine = create_engine(
                url_object, pool_size=20, max_overflow=0
            ).execution_options(autocommit=True)
            return sessionmaker(
                bind=connection_engine, autocommit=False, autoflush=False
            )
        except Exception as e:
            logger.error(f"Error creating postgresql engine: {e}")
            return None

    @staticmethod
    def _conn_postgres_psycopg2():
        try:
            conn = psycopg2.connect(
                host=database_settings.POSTGRES_HOST,
                database=database_settings.POSTGRES_DB_NAME,
                user=database_settings.POSTGRES_USERNAME,
                password=database_settings.POSTGRES_PASSWORD,
                port=database_settings.POSTGRES_PORT,
                cursor_factory=RealDictCursor,
            )
            return conn
        except psycopg2.Error as e:
            logger.error(f"Error connecting to the database: {e}")
            return None
