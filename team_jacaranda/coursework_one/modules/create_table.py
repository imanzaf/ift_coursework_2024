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

# SQL query to check if the table exists
check_table_exists_query = """
SELECT EXISTS (
    SELECT 1 
    FROM information_schema.tables 
    WHERE table_schema = 'csr_reporting' 
    AND table_name = 'company_reports'
);
"""

# SQL query to create a new table with foreign key constraint
create_table_query = """
CREATE TABLE csr_reporting.company_reports (
    id SERIAL,
    symbol CHAR(12),
    security TEXT,
    report_url VARCHAR(255),
    report_year INTEGER,
    minio_path VARCHAR(255),
    PRIMARY KEY (id)
)
"""

# Connect to PostgreSQL database and create new table if it does not exist
try:
    # Connect to the database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Check if the table exists
    cursor.execute(check_table_exists_query)
    table_exists = cursor.fetchone()[0]

    if table_exists:
        print("Table csr_reporting.company_reports already exists.")
    else:
        # Execute the SQL query to create the table
        cursor.execute(create_table_query)
        cursor.execute("""
        SELECT symbol, security FROM csr_reporting.company_static
        ORDER BY symbol;
    """)
        companies = cursor.fetchall()

        for symbol, security in companies:
            cursor.execute("""
                INSERT INTO csr_reporting.company_reports (symbol, security)
                VALUES (%s, %s)
                ON CONFLICT DO nothing;
            """, (symbol, security))

    # Commit the transaction
    conn.commit()
    print("Table csr_reporting.company_reports created successfully!")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the database connection
    if conn:
        cursor.close()
        conn.close()