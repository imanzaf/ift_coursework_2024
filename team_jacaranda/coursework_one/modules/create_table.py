import psycopg2
from psycopg2 import sql

# PostgreSQL database connection configuration
db_config = {
    "dbname": "fift",
    "user": "postgres",
    "password": "postgres",
    "host": "host.docker.internal",
    "port": 5439
}

# SQL query to create a new table with foreign key constraint
create_table_query = """
CREATE TABLE IF NOT EXISTS csr_reporting.company_reports (
    id SERIAL PRIMARY KEY,
    security TEXT,
    report_url VARCHAR(255),
    report_year INTEGER,
    minio_path VARCHAR(255),
    FOREIGN KEY (security) REFERENCES csr_reporting.company_static (security)
)
"""

# Connect to PostgreSQL database and create new table
try:
    # Connect to the database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Execute the SQL query to create the table
    cursor.execute(create_table_query)

    # Commit the transaction
    conn.commit()
    print("Table csr_reporting.csr_reports created successfully (if not exists) with foreign key constraint!")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the database connection
    if conn:
        cursor.close()
        conn.close()
