import os
import re
import datetime
import pdfplumber
import magic
from pymongo import MongoClient
from minio import Minio

# ========== 配置区 ==========
MONGO_URI = "mongodb://localhost:27019"
MONGO_DB_NAME = "csr_db"
MONGO_COLLECTION = "csr_reports"

MINIO_CLIENT = Minio(
    "localhost:9000",
    access_key="ift_bigdata",
    secret_key="minio_password",
    secure=False,
)
BUCKET_NAME = "csr-reports"

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
collection_reports = mongo_db[MONGO_COLLECTION]

# ========== 日志功能 ==========
LOG_FILE = "csr_fix_and_cleanup.log"


def write_log(message):
    """记录日志到文件和终端"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")


# ========== 工具函数 ==========
def is_valid_pdf(file_path):
    """检查文件是否为有效的 PDF"""
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    return file_type == "application/pdf"


def delete_invalid_pdf_from_minio(object_name):
    """从 MinIO 删除损坏的 PDF"""
    try:
        MINIO_CLIENT.remove_object(BUCKET_NAME, object_name)
        write_log(f"🗑️ 删除损坏文件: {object_name}")
    except Exception as e:
        write_log(f"⚠️ 删除 {object_name} 失败: {e}")


def download_pdf_from_minio(object_name, local_path):
    """从 MinIO 下载 PDF，并检查是否为有效 PDF"""
    try:
        MINIO_CLIENT.fget_object(BUCKET_NAME, object_name, local_path)
        if not is_valid_pdf(local_path):
            write_log(f"⚠️ {object_name} 不是有效 PDF，删除")
            os.remove(local_path)
            delete_invalid_pdf_from_minio(object_name)
            return False
        return True
    except Exception as e:
        write_log(f"❌ 下载 {object_name} 失败: {e}")
        return False


def extract_year_from_pdf(file_path):
    """从 PDF 中提取年份(只扫前两页)"""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:2]:
                text = page.extract_text() or ""
                match = re.search(r"20\d{2}", text)
                if match:
                    return int(match.group(0))
    except Exception as e:
        write_log(f"❌ 解析 {file_path} 失败: {e}")
    return None


# ========== 任务 1: 修正 CSR 报告年份 ==========
def update_csr_year():
    """从 MinIO 下载 PDF，解析年份，并更新 MongoDB"""
    reports = collection_reports.find()
    local_dir = "./reports"
    os.makedirs(local_dir, exist_ok=True)

    for doc in reports:
        company_name = doc["company_name"]
        object_name = doc["storage_path"]
        local_path = os.path.join(local_dir, object_name.replace("/", "_"))

        write_log(f"📥 处理 {company_name} 的 PDF: {object_name}")
        if not download_pdf_from_minio(object_name, local_path):
            continue  # 如果下载失败或不是PDF，跳过

        actual_year = extract_year_from_pdf(local_path)
        if actual_year:
            collection_reports.update_one(
                {"_id": doc["_id"]}, {"$set": {"csr_report_year": actual_year}}
            )
            write_log(f"✅ 更新 {company_name} 年份为 {actual_year}")
        else:
            write_log(f"⚠️ {company_name} 解析年份失败")

        if os.path.exists(local_path):
            os.remove(local_path)


# ========== 任务 2: 统一修正 ingestion_time ==========
def fix_ingestion_time():
    """将 ingestion_time 字段统一转换为字符串格式"""
    reports = collection_reports.find()
    for doc in reports:
        ingestion_time = doc.get("ingestion_time")
        if isinstance(ingestion_time, datetime.datetime):
            collection_reports.update_one(
                {"_id": doc["_id"]},
                {"$set": {"ingestion_time": ingestion_time.isoformat()}},
            )
            write_log(f"✅ 修正 {doc['company_name']} 的 ingestion_time 为字符串格式")


# ========== 任务 3: 删除真正的重复 PDF (相同公司 + 相同年份) ==========
def delete_duplicate_pdfs():
    """
    如果 (company_name, csr_report_year) 完全相同，保留最先出现的一份，删除后来的文件。
    """
    all_docs = list(collection_reports.find())
    seen = {}

    for doc in all_docs:
        comp = doc["company_name"]
        year = doc.get("csr_report_year", None)
        obj_path = doc["storage_path"]
        doc_id = doc["_id"]

        if year is None:
            continue

        key = (comp, year)
        if key not in seen:
            seen[key] = doc_id
        else:
            write_log(f"🗑️ 发现重复: {comp}({year}), 删除 {obj_path}")
            try:
                MINIO_CLIENT.remove_object(BUCKET_NAME, obj_path)
                write_log(f"✅ 已删除 {obj_path}")
            except Exception as e:
                write_log(f"⚠️ 删除 {obj_path} 失败: {e}")
            collection_reports.delete_one({"_id": doc_id})


# ========== 主程序 ==========
def main():
    write_log("🚀 开始修正 CSR 报告年份...")
    update_csr_year()

    write_log("🚀 开始修正 ingestion_time...")
    fix_ingestion_time()

    write_log("🚀 开始删除重复的 CSR 报告...")
    delete_duplicate_pdfs()

    write_log("🎉 所有任务完成！")


if __name__ == "__main__":
    main()
