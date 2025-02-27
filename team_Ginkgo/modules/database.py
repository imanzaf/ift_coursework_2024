'''
This script creates a table in the database to store the companies and their CSR reports.
It first establishes a connection to the database using the psycopg2 library and the database configuration settings.
It then creates a schema named "Ginkgo" if it does not already exist.   
Next, it creates a table named "csr_reports" with columns for the company symbol, company name, report year, report URL, and Minio path.
After creating the table, it selects all companies from the "company_static" table and inserts each company starting from the year 2014 into the "csr_reports" table.
The script uses the "ON CONFLICT DO nothing" clause to avoid inserting duplicate records.
Finally, it commits the changes and closes the database connection.
The script prints a success message after successfully inserting the companies into the "csr_reports" table.

'''
import psycopg2
from config import DB_CONFIG

def insert_companies():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Design schema and table
    cursor.execute("CREATE SCHEMA IF NOT EXISTS Ginkgo;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ginkgo.csr_reports (
            symbol VARCHAR(50),
            company_name TEXT NOT NULL,
            report_year INT NOT NULL,
            report_url TEXT,    
            minio_path TEXT,
            PRIMARY KEY (symbol, report_year)     
        );
    """)

    conn.commit()
    print("✅ Database setup completed!")

    # Select all companies (column name `security` corresponds to company name)
    cursor.execute("""
        SELECT symbol, security FROM csr_reporting.company_static
        ORDER BY symbol;
    """)
    companies = cursor.fetchall()

    for symbol, security in companies:
        for year in range(2014, 2024):
            cursor.execute("""
                   INSERT INTO Ginkgo.csr_reports (symbol, company_name, report_year)
                   VALUES (%s, %s, %s)
                   ON CONFLICT DO nothing;
               """, (symbol, security, year))

    conn.commit()
    cursor.close()
    conn.close()
    print("Successfully inserted companies into csr_reports")

# Run
if __name__ == "__main__":
   insert_companies()

