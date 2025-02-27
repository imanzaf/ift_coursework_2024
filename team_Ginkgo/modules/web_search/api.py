'''
This module provides a FastAPI server to query CSR reports from the database.
Example usage:
    - Query CSR report by company name: http://
    - Query CSR report by stock symbol: http://
    
To start the server, run:
    $ python api.py

'''
from fastapi import FastAPI, HTTPException
import psycopg2
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DB_CONFIG
app = FastAPI()

# Connect to the database
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Query CSR report
@app.get("/report")
def get_csr_report(query: str, year: int):
    """
    Query CSR report
    - query: Company name (company_name) or Stock symbol (symbol)
    - year: Report year
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

# Start API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
