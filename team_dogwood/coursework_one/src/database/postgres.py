"""
TODO -
    - Methods for writing company details to sql database (postrgres)
    - Methods for loading company data from sql database (postrgres)
"""

from typing import Dict

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text

from config.postgres import postgres_settings
from src.data_models.company import Company


class PostgreSQLDB(BaseModel):
    """ """

    sql_config: Dict = Field(..., description="SQL configuration dict")

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    @property
    def connection(self):
        engine = self._conn_postgres()
        return sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def commit(self):
        self.connection.commit()

    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, ops_type, sql_statement=None, data_load=None):
        """
        TODO - understand and fix!!
        """
        Session = scoped_session(self._conn)
        s = Session()
        if ops_type == "upsert":
            stmt = insert(Company).values(data_load)
            stmt = stmt.on_conflict_do_update(
                index_elements=["pos_id"],
                set_=dict(
                    {
                        "net_amount": stmt.excluded.net_amount,
                        "net_quantity": stmt.excluded.net_quantity,
                    }
                ),
            )
            output = s.execute(stmt)
            self.commit()
            return output.is_insert
        elif ops_type == "read":
            output = self.execute(text(sql_statement))
            return output.mappings().all()
        else:
            raise TypeError("Database method not supported. Only read and write.")

    @staticmethod
    def _conn_postgres():
        url_object = engine.URL.create(
            drivername=postgres_settings.DRIVER,
            username=postgres_settings.USERNAME,
            password=postgres_settings.PASSWORD,
            host=postgres_settings.HOST,
            database=postgres_settings.DB,
            port=postgres_settings.HOST,
        )
        try:
            connection_engine = create_engine(
                url_object, pool_size=20, max_overflow=0
            ).execution_options(autocommit=True)
            return connection_engine
        except Exception as genericErr:
            raise Exception(
                "Error occurred while attempting to create postgresql engine"
            ) from genericErr
