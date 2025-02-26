import pytest
import psycopg2
from psycopg2.extras import RealDictCursor


DB_HOST = "localhost"  
DB_PORT = 5439         
DB_NAME = "postgres"    
DB_USER = "postgres"
DB_PASSWORD = "postgres"


@pytest.fixture(scope="module")
def db_connection():

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name TEXT
            );
        """)
        conn.commit()


    yield conn

    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_table;")
        conn.commit()
    conn.close()


def test_postgres_insert(db_connection):
    """
    test data which insterted inti test_table
    """
    with db_connection.cursor() as cur:
        cur.execute("INSERT INTO test_table (name) VALUES ('Hello Postgres') RETURNING id;")
        new_id = cur.fetchone()[0]
    db_connection.commit()

    assert new_id is not None, "Insertion failed without returning the ID of the new record。"


def test_postgres_query(db_connection):
    """
    Test if you can query the previously inserted data
    """
    with db_connection.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM test_table WHERE name = 'Hello Postgres';")
        row = cur.fetchone()

    assert row is not None, "Inserted data not queried."
    assert row["name"] == "Hello Postgres", "Mismatch between 'name' and insert in query result."


def test_postgres_delete(db_connection):
    """
    Test to see if the data can be deleted correctly
    """
    with db_connection.cursor() as cur:
        cur.execute("DELETE FROM test_table WHERE name = 'Hello Postgres';")
    db_connection.commit()

    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM test_table WHERE name = 'Hello Postgres';")
        row = cur.fetchone()

    assert row is None, "Data deletion fails and records can still be queried."
