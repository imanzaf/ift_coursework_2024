"""
web_search.api module

This module defines the FastAPI application and endpoints for querying CSR reports.

Author: Your Name
Version: 1.0.0
License: MIT License
"""

from fastapi import FastAPI, HTTPException
import psycopg2
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DB_CONFIG

app = FastAPI()

def get_db_connection():
    """
    Establish a connection to the PostgreSQL database using the configuration provided in DB_CONFIG.

    Returns:
        psycopg2.extensions.connection: A connection object to the database.
    """
    return psycopg2.connect(**DB_CONFIG)

@app.get("/report")
def get_csr_report(query: str, year: int):
    """
    Query CSR report based on the provided company name or stock symbol and year.

    Args:
        query (str): Company name (company_name) or Stock symbol (symbol).
        year (int): Report year.

    Returns:
        list: A list of dictionaries containing the company name, symbol, report URL, and MinIO path.
        dict: A dictionary with a message if no CSR report is found.

    Raises:
        HTTPException: If an error occurs during the database operation.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Allow querying by company_name or symbol
        query_sql = """
        SELECT company_name, symbol, report_url, minio_path 
        FROM ginkgo.csr_reports 
        WHERE (company_name ILIKE %s OR symbol ILIKE %s) 
        AND report_year = %s;
        """
        cur.execute(query_sql, (f"%{query}%", f"%{query}%", year))
        result = cur.fetchmany(20)
        cur.close()
        conn.close()

        if result:
            return [
                {
                    "company_name": row[0],
                    "symbol": row[1],
                    "report_url": row[2],
                    "minio_path": row[3]
                }
                for row in result
            ]
        else:
            return {"message": "CSR report not found for the company"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    """
    Main entry point to start the FastAPI server.

    This script uses the `uvicorn` module to run the FastAPI application
    on host `0.0.0.0` and port `8000`.
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
