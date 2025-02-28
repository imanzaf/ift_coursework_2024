from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import logging
import shutil

# ==========================
# 1. Logging Setup
# ==========================
logging.basicConfig(level=logging.INFO)

# ==========================
# 2. MongoDB Connection
# ==========================
MONGO_URI = "mongodb://localhost:27019"
MONGO_DB_NAME = "csr_db"
MONGO_COLLECTION = "csr_reports"

# 直接调用 MongoClient，让 mock_mongo_client 可以被测试捕获
logging.info("🔌 Initializing MongoDB client...")
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
mongo_db = mongo_client[MONGO_DB_NAME]
collection_reports = mongo_db[MONGO_COLLECTION]
logging.info("✅ MongoDB client initialized.")

# ==========================
# 3. MinIO Config
# ==========================
MINIO_HOST = os.getenv("MINIO_HOST", "localhost")
MINIO_BUCKET = "csr-reports"

# ==========================
# 4. Initialize FastAPI
# ==========================
app = FastAPI(
    title="CSR Reports API",
    description="Retrieve CSR reports with search and batch download features.",
    version="1.0",
)

# ==========================
# 5. Data Models
# ==========================
class CSRReport(BaseModel):
    company_name: str
    csr_report_url: str
    storage_path: str
    csr_report_year: int
    ingestion_time: str  # store as string
    download_link: Optional[str] = None

class BatchDownloadRequest(BaseModel):
    report_paths: List[str]

# ==========================
# 6. GET /reports (Fuzzy search)
# ==========================
@app.get("/reports", response_model=List[CSRReport])
def get_reports(
    company: Optional[str] = Query(None, description="Company name (fuzzy)"),
    year: Optional[int] = Query(None, description="Report year, e.g., 2023"),
):
    """
    Retrieve CSR reports by company name (supports partial match) and/or report year.
    """
    try:
        query = {}
        if company:
            query["company_name"] = {"$regex": company, "$options": "i"}
        if year:
            query["csr_report_year"] = year

        logging.info(f"🔍 Querying MongoDB with: {query}")
        reports = list(collection_reports.find(query, {"_id": 0}))

        if not reports:
            logging.warning(f"⚠️ No results found for query: {query}")
            # 抛出 404 而不是继续进入 except Exception
            raise HTTPException(status_code=404, detail="No reports found for the given query")

        # Build download_link & convert ingestion_time to str
        results = []
        for report in reports:
            # Ensure ingestion_time is str
            if isinstance(report.get("ingestion_time"), datetime):
                report["ingestion_time"] = report["ingestion_time"].isoformat()

            # Construct MinIO download link
            if "storage_path" in report:
                report["download_link"] = f"http://{MINIO_HOST}:9000/{MINIO_BUCKET}/{report['storage_path']}"

            results.append(report)

        return results

    except HTTPException as http_ex:
        # 重新抛出 HTTPException，让测试得到正确的 status_code
        logging.error(f"❌ {http_ex.status_code}: {http_ex.detail}")
        raise http_ex

    except Exception as e:
        logging.error(f"❌ Internal Server Error: {e}")
        # 返回 500
        raise HTTPException(status_code=500, detail=str(e))

# ==========================
# 7. POST /download-zip (Batch download)
# ==========================
@app.post("/download-zip")
async def download_reports(request: BatchDownloadRequest):
    """
    Batch download multiple CSR reports as a ZIP file.
    """
    try:
        if not request.report_paths:
            # 如果没有传任何文件，抛出 400
            raise HTTPException(status_code=400, detail="No reports selected for download")

        temp_dir = "./temp_reports"
        zip_file_path = "./csr_reports.zip"

        # Clean up old files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        # Download files
        for report_path in request.report_paths:
            file_name = report_path.split("/")[-1]
            local_path = os.path.join(temp_dir, file_name)

            # In real usage, use MinIO client fget_object
            # MINIO_CLIENT.fget_object(MINIO_BUCKET, report_path, local_path)

            # Here, we mock the file for testing
            with open(local_path, "w") as f:
                f.write("Dummy PDF content")

        # Pack into ZIP
        shutil.make_archive(zip_file_path.replace(".zip", ""), "zip", temp_dir)

        return FileResponse(
            zip_file_path,
            filename="csr_reports.zip",
            media_type="application/zip"
        )

    except HTTPException as http_ex:
        # 如果是 HTTPException(400)，说明 “No files”
        logging.error(f"❌ Batch download error: {http_ex.status_code}: {http_ex.detail}")
        raise http_ex

    except Exception as e:
        logging.error(f"❌ Batch download error: {e}")
        # 其他未知错误 -> 500
        raise HTTPException(status_code=500, detail=str(e))

# ==========================
# 8. Run the API
# ==========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_api:app", host="0.0.0.0", port=8000, reload=True)
