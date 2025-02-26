"""
Methods for interacting with postgres database.
"""

import os
import sys

import psycopg2
from loguru import logger
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from sqlalchemy import create_engine, engine

# from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker  # scoped_session

# from src.data_models.company import Company
from sqlalchemy.sql import text

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from config.db import database_settings

# from src.data_models.company import Company


class PostgreSQLDB(BaseModel):
    """
    Methods for connecting to and interacting with the PostgreSQL database.

    This class provides methods for connecting to a PostgreSQL database, executing SQL operations,
    and managing database sessions. It supports both read and upsert (update/insert) operations.

    :param BaseModel: Inherits from Pydantic's BaseModel for data validation and settings management.

    Example:
        >>> db = PostgreSQLDB()
        >>> with db:
        ...     db.execute("read", sql_statement="SELECT * FROM companies")
    """

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        :return: The instance of the PostgreSQLDB class.
        :rtype: PostgreSQLDB
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context and close the database connection.

        :param exc_type: The exception type (if any).
        :param exc_val: The exception value (if any).
        :param exc_tb: The traceback (if any).
        """
        if exc_type is None:  # No exceptions → commit the transaction
            self.session.commit()
        else:
            self.session.rollback()  # Rollback on error
        self.session.close()

    @property
    def session(self):
        """
        Create and return a SQLAlchemy session for database interactions.

        :return: A SQLAlchemy sessionmaker object.
        :rtype: sqlalchemy.orm.sessionmaker
        """
        Session = self._conn_postgres()
        logger.debug("Connection to PostgreSQL database established.")
        return Session()

    def execute(self, query, params=None):
        """Fetches data (SELECT) and returns a list of dictionaries."""
        if self.session is None:
            logger.error(
                f"No connection to the database {database_settings.POSTGRES_DB_NAME}."
            )
            return []
        try:
            logger.info(f"Executing query: {query}...")
            logger.debug(f"Connected to DataBase: {self.session.bind.url.database}")
            result = self.session.execute(text(query), params or {})
            rows = result.fetchall()
            self.session.commit()
            logger.debug(f"Fetched data: {rows}")
            return rows
        except Exception as e:
            logger.error(f"Database error: {e}")
            return []

    def store_csr_report(self, company_id, report_url, report_year):
        """
        Inserts a new CSR report record into the database.
        If (company_id, report_year) is unique, we use ON CONFLICT to avoid duplicates.
        Adjust if you have a primary key like 'report_id serial primary key'.
        """
        query = """
        INSERT INTO csr_reporting.company_csr_reports (company_id, report_url, report_year, retrieved_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (company_id, report_year) DO NOTHING
        """
        self.execute(query, (company_id, report_url, report_year))

    def get_csr_reports_by_company(self, company_id):
        """
        Retrieve all CSR reports for a specific company, ordered by year desc.
        """
        query = """
        SELECT *
        FROM csr_reporting.company_csr_reports
        WHERE company_id = %s
        ORDER BY report_year DESC
        """
        return self.execute(query, (company_id,))

    def get_csr_report_by_id(self, report_id):
        """
        Fetch a single CSR report by its primary key (report_id).
        (Assumes you have a 'report_id' column in your table.)
        """
        query = """
        SELECT *
        FROM csr_reporting.company_csr_reports
        WHERE report_id = %s
        """
        results = self.execute(query, (report_id,))
        return results[0] if results else None

    def update_csr_report(self, report_id, new_url=None, new_year=None):
        """
        Updates a CSR report's URL and/or year based on report_id.
        Only updates fields that are provided.
        """
        # Build dynamic query
        fields = []
        params = []

        if new_url is not None:
            fields.append("report_url = %s")
            params.append(new_url)
        if new_year is not None:
            fields.append("report_year = %s")
            params.append(new_year)

        # If no fields to update, just return
        if not fields:
            print("No fields to update.")
            return

        set_clause = ", ".join(fields)
        params.append(report_id)  # for WHERE clause

        query = f"""
        UPDATE csr_reporting.company_csr_reports
        SET {set_clause}
        WHERE report_id = %s
        """

        self.execute(query, tuple(params))

    def delete_csr_report(self, report_id):
        """
        Deletes a CSR report record from the database by report_id.
        """
        query = """
        DELETE FROM csr_reporting.company_csr_reports
        WHERE report_id = %s
        """
        self.execute(query, (report_id,))

    @staticmethod
    def _conn_postgres():
        """
        Create a connection engine for PostgreSQL.

        :return: A SQLAlchemy engine object.
        :rtype: sqlalchemy.engine.Engine
        :raises Exception: If an error occurs while creating the engine.
        """
        url_object = engine.URL.create(
            drivername=database_settings.POSTGRES_DRIVER,
            username=database_settings.POSTGRES_USERNAME,
            password=database_settings.POSTGRES_PASSWORD,
            host=database_settings.POSTGRES_HOST,
            database=database_settings.POSTGRES_DB_NAME,
            port=database_settings.POSTGRES_PORT,
        )
        try:
            logger.debug("Connecting to the PostgreSQL database...")
            connection_engine = create_engine(
                url_object, pool_size=20, max_overflow=0
            ).execution_options(autocommit=True)
            return sessionmaker(
                bind=connection_engine, autocommit=False, autoflush=False
            )
        except Exception as e:
            logger.error(
                f"Error occurred while attempting to create postgresql engine: {e}"
            )
            return None

    @staticmethod
    def _conn_postgres_psycopg2():
        """Establishes a raw psycopg2 connection to PostgreSQL."""
        try:
            logger.debug("Connecting to the PostgreSQL database...")
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
