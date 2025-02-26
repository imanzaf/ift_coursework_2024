
from pydantic import BaseModel
from sqlalchemy import create_engine, engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text

from config.db import database_settings
from src.data_models.company import Company


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

    def __exit__(self):
        """
        Exit the runtime context and close the database connection.

        :param exc_type: The exception type (if any).
        :param exc_val: The exception value (if any).
        :param exc_tb: The traceback (if any).
        """
        self.close()

    @property
    def connection(self):
        """
        Create and return a SQLAlchemy session for database interactions.

        :return: A SQLAlchemy sessionmaker object.
        :rtype: sqlalchemy.orm.sessionmaker
        """
        engine = self._conn_postgres()
        return sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def commit(self):
        """
        Commit the current transaction.
        """
        self.connection.commit()

    def close(self, commit=True):
        """
        Close the database connection.

        :param commit: Whether to commit the transaction before closing. Defaults to True.
        :type commit: bool
        """
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, ops_type, sql_statement=None, data_load=None):
        """
        Execute a database operation (read or upsert).

        :param ops_type: The type of operation to perform. Supported values are "read" and "upsert".
        :type ops_type: str
        :param sql_statement: The SQL statement to execute (required for "read" operations).
        :type sql_statement: str, optional
        :param data_load: The data to upsert into the database (required for "upsert" operations).
        :type data_load: dict, optional
        :return: For "read" operations, returns the query results. For "upsert" operations, returns whether the operation was an insert.
        :rtype: list or bool
        :raises TypeError: If the operation type is not supported.
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
            connection_engine = create_engine(
                url_object, pool_size=20, max_overflow=0
            ).execution_options(autocommit=True)
            return connection_engine
        except Exception as genericErr:
            raise Exception(
                "Error occurred while attempting to create postgresql engine"
            ) from genericErr
