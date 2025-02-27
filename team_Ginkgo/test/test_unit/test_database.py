import pytest
import psycopg2
import subprocess
import sys
import os

# Dynamically add the path to the source files
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../modules")))

from config import DB_CONFIG
from database import insert_companies

def get_db_connection():
    """Establish database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_database_connection():
    """Test if the database connection is successful."""
    conn = get_db_connection()
    assert conn is not None, "❌ Database connection failed!"
    conn.close()
    print("✅ Database connection successful.")

def test_schema_and_table():
    """Test if schema 'Ginkgo' and table 'csr_reports' exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE LOWER(schema_name) = 'ginkgo';")
    schema_exists = cursor.fetchone()

    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE LOWER(table_schema) = 'ginkgo' AND LOWER(table_name) = 'csr_reports';
    """)
    table_exists = cursor.fetchone()

    cursor.close()
    conn.close()

    assert schema_exists, "❌ Schema 'Ginkgo' does not exist."
    assert table_exists, "❌ Table 'csr_reports' does not exist."
    print("✅ Schema and table exist.")

def test_data_insertion():
    """Test if companies are successfully inserted into Ginkgo.csr_reports."""
    conn = get_db_connection()
    cursor = conn.cursor()

    insert_companies()
    
    cursor.execute("SELECT COUNT(*) FROM Ginkgo.csr_reports;")
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()

    assert count > 0, "❌ No data inserted into Ginkgo.csr_reports."
    print(f"✅ Data insertion successful. {count} records found.")

def test_primary_key_constraint():
    """Test if duplicate insertions are prevented by ON CONFLICT DO NOTHING."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Ginkgo.csr_reports;")
    before_count = cursor.fetchone()[0]

    insert_companies()

    cursor.execute("SELECT COUNT(*) FROM Ginkgo.csr_reports;")
    after_count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()

    assert before_count == after_count, "❌ Duplicate records were inserted!"
    print("✅ Primary key constraint working correctly. No duplicates inserted.")

def test_code_quality():
    """Run linting, formatting, and security scans for database.py only."""
    python_exec = sys.executable  # Get the correct Python path
    database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../modules/database.py"))

    print("🔍 Running flake8 on database.py...")
    subprocess.run([python_exec, "-m", "flake8", database_path, "--max-line-length=100"], check=True)

    print("🔍 Checking code formatting with black...")
    subprocess.run([python_exec, "-m", "black", "--check", database_path], check=True)

    print("🔍 Sorting imports with isort...")
    subprocess.run([python_exec, "-m", "isort", "--check-only", database_path], check=True)

    print("🔍 Running security scans with Bandit...")
    subprocess.run([python_exec, "-m", "bandit", "-r", database_path], check=True)

if __name__ == "__main__":
    test_database_connection()
    test_schema_and_table()
    test_data_insertion()
    test_primary_key_constraint()
    test_code_quality()
