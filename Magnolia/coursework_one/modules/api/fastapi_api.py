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
# 1. 设置日志
# ==========================
logging.basicConfig(level=logging.INFO)

# ==========================
# 2. MongoDB 连接
# ==========================
MONGO_URI = "mongodb://localhost:27019"
MONGO_DB_NAME = "csr_db"
MONGO_COLLECTION = "csr_reports"

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)  # 设置超时
    mongo_db = mongo_client[MONGO_DB_NAME]
    collection_reports = mongo_db[MONGO_COLLECTION]
    mongo_client.server_info()  # 测试 MongoDB 连接
    logging.info("✅ Connected to MongoDB")
except Exception as e:
    logging.error(f"❌ MongoDB Connection Error: {e}")
    raise e

# ==========================
# 3. MinIO 配置
# ==========================
MINIO_HOST = os.getenv("MINIO_HOST", "localhost")
MINIO_BUCKET = "csr-reports"

# ==========================
# 4. 初始化 FastAPI
# ==========================
app = FastAPI(
    title="CSR Reports API",
    description="Retrieve CSR reports with search and batch download features.",
    version="1.0",
)


# ==========================
# 5. 数据模型
# ==========================
class CSRReport(BaseModel):
    company_name: str
    csr_report_url: str
    storage_path: str
    csr_report_year: int
    ingestion_time: str  # 确保是字符串格式
    download_link: Optional[str] = None


class BatchDownloadRequest(BaseModel):
    report_paths: List[str]


# ==========================
# 6. CSR 报告查询 API（支持模糊搜索）
# ==========================
@app.get("/reports", response_model=List[CSRReport])
def get_reports(
    company: Optional[str] = Query(
        None, description="Company name (supports partial match)"
    ),
    year: Optional[int] = Query(None, description="Report year, e.g., 2023"),
):
    """
    Retrieve CSR reports by company name (supports fuzzy search) and/or report year.
    """
    try:
        query = {}
        if company:
            query["company_name"] = {
                "$regex": company,
                "$options": "i",
            }  # 模糊搜索（不区分大小写）
        if year:
            query["csr_report_year"] = year

        logging.info(f"🔍 Querying MongoDB with: {query}")

        reports = list(collection_reports.find(query, {"_id": 0}))

        if not reports:
            logging.warning(f"⚠️ No results found for query: {query}")
            raise HTTPException(
                status_code=404, detail="No reports found for the given query"
            )

        results = []
        for report in reports:
            # 处理 ingestion_time 字段，确保是字符串格式
            if isinstance(report["ingestion_time"], datetime):
                report["ingestion_time"] = report["ingestion_time"].isoformat()

            # 构造 MinIO 下载链接
            if "storage_path" in report:
                report["download_link"] = (
                    f"http://{MINIO_HOST}:9000/{MINIO_BUCKET}/{report['storage_path']}"
                )

            results.append(report)

        return results

    except Exception as e:
        logging.error(f"❌ Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================
# 7. 批量下载 ZIP
# ==========================
@app.post("/download-zip")
async def download_reports(request: BatchDownloadRequest):
    """
    Batch download multiple CSR reports as a ZIP file.
    """
    try:
        if not request.report_paths:
            raise HTTPException(
                status_code=400, detail="No reports selected for download"
            )

        # 创建临时目录
        temp_dir = "./temp_reports"
        zip_file_path = "./csr_reports.zip"

        # 清理旧文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        # 下载选中的报告
        for report_path in request.report_paths:
            file_name = report_path.split("/")[-1]
            local_path = os.path.join(temp_dir, file_name)

            # 这里 MinIO 客户端应该下载文件（请确保 MinIO 客户端已正确配置）
            # MINIO_CLIENT.fget_object(BUCKET_NAME, report_path, local_path)

            # 这里暂时模拟下载
            with open(local_path, "w") as f:
                f.write("Dummy PDF content")  # 这里只是模拟，正式环境请改为真实下载逻辑

        # 打包成 ZIP
        shutil.make_archive(zip_file_path.replace(".zip", ""), "zip", temp_dir)

        return FileResponse(
            zip_file_path, filename="csr_reports.zip", media_type="application/zip"
        )

    except Exception as e:
        logging.error(f"❌ Batch download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================
# 8. 启动 API
# ==========================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("csr_api:app", host="0.0.0.0", port=8000, reload=True)
