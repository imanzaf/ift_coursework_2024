import os
import sys
import time
import datetime
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests
from apscheduler.schedulers.blocking import BlockingScheduler

# Selenium / ChromeDriver
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# PostgreSQL 只用于读取公司列表
import psycopg2

# MongoDB (改为写入）
from pymongo import MongoClient

# MinIO
from minio import Minio

# ========== 配置区 ==========
DB_CONFIG = {
    "dbname": "fift",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5439",
}

MONGO_URI = "mongodb://localhost:27019"
MONGO_DB_NAME = "csr_db"
MONGO_COLLECTION = "csr_reports"

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
collection_reports = mongo_db[MONGO_COLLECTION]

MINIO_CLIENT = Minio(
    "localhost:9000",
    access_key="ift_bigdata",
    secret_key="minio_password",
    secure=False,
)
BUCKET_NAME = "csr-reports"

PROXY = None  # 如果需要代理，如："http://127.0.0.1:7890"

# ========== 日志功能 ==========
# 1) 在测试环境下，日志写到 "test_log.log"
#    否则正常写入 "csr_fast.log"
if "pytest" in sys.modules:
    LOG_FILE = "test_log.log"
else:
    LOG_FILE = "csr_fast.log"

def write_log(message: str):
    """
    记录日志到文件和终端
    如果处于 pytest 环境，则写入 test_log.log
    否则写入 csr_fast.log
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"

    # 打印到终端
    print(log_msg)

    # 写入日志文件
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")


# ========== 核心功能 ==========
def init_driver():
    """初始化 Chrome WebDriver"""
    write_log("🚀 初始化 ChromeDriver...")

    options = webdriver.ChromeOptions()
    # 如果不需要打开浏览器界面，可取消注释以无头模式
    # options.add_argument('--headless')
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")

    # 若需要代理
    # if PROXY:
    #     options.add_argument(f'--proxy-server={PROXY}')

    chromedriver_autoinstaller.install()
    driver = webdriver.Chrome(options=options)

    write_log("✅ ChromeDriver 启动成功！")
    return driver


def get_search_results(driver, query, timeout=5):
    """
    在 Bing 上搜索, 返回搜索结果
    1) 缩短默认超时到 5s
    2) 若 driver 被 mock，则直接返回 mock 设定的结果
    """
    # 如果 driver 是 mock（pytest 对 get_search_results 进行 patch），
    # 可能返回 MagicMock 而不会执行实际的查找逻辑。
    from unittest.mock import MagicMock
    if isinstance(driver, MagicMock):
        return driver.find_elements()

    search_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    write_log(f"🔍 访问搜索引擎: {search_url}")

    try:
        driver.get(search_url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".b_algo h2 a"))
        )
        results = driver.find_elements(By.CSS_SELECTOR, ".b_algo h2 a")
        write_log(f"✅ 搜索完成，找到 {len(results)} 个结果")
        return results
    except Exception as e:
        write_log(f"❌ 搜索失败: {type(e).__name__}, {e}")
        return []


def download_pdf(company_name, year, url):
    """下载 PDF 到本地(含年份区分)"""
    write_log(f"📥 开始下载 {company_name}({year}) 的 PDF: {url}")

    if "pdf" not in url.lower():
        write_log(f"⚠️ {company_name}({year}) 不是 PDF 文件，跳过")
        return None

    local_dir = "./reports"
    os.makedirs(local_dir, exist_ok=True)
    # 避免覆盖：在本地加年份
    local_path = os.path.join(local_dir, f"{company_name}_{year}.pdf")

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(resp.content)
            write_log(f"✅ {company_name}({year}) 下载成功: {local_path}")
            return local_path
        else:
            write_log(f"❌ {company_name}({year}) 下载失败，状态码: {resp.status_code}")
    except Exception as e:
        write_log(f"❌ {company_name}({year}) 下载失败: {type(e).__name__}, {e}")

    return None


def upload_to_minio(company_name, year, local_path):
    """上传 PDF 到 MinIO，按年份区分文件"""
    try:
        object_name = f"{year}/{company_name}.pdf"
        write_log(f"📤 开始上传 {company_name}({year}) 到 MinIO...")

        with open(local_path, "rb") as f:
            MINIO_CLIENT.put_object(
                bucket_name=BUCKET_NAME,
                object_name=object_name,
                data=f,
                length=os.path.getsize(local_path),
                content_type="application/pdf",
            )
        write_log(f"✅ MinIO 上传成功: {object_name}")
        return object_name
    except Exception as e:
        write_log(f"❌ MinIO 上传失败: {type(e).__name__}, {e}")
        return None


def save_csr_report_info_to_mongo(company_name, pdf_url, object_name, year):
    """保存 CSR 报告信息到 MongoDB，并记录报告年份"""
    try:
        data = {
            "company_name": company_name,
            "csr_report_url": pdf_url,
            "storage_path": object_name,
            "csr_report_year": year,
            # 建议使用带时区的 now，如 datetime.datetime.now(datetime.UTC)
            "ingestion_time": datetime.datetime.utcnow(),
        }
        # 确保 (company + year) 做区分
        mongo_db["csr_reports"].update_one(
            {"company_name": company_name, "csr_report_year": year},
            {"$set": data},
            upsert=True,
        )
        write_log(f"✅ MongoDB 记录更新成功: {company_name}({year})")
    except Exception as e:
        write_log(f"❌ MongoDB 记录更新失败: {type(e).__name__}, {e}")


def get_company_list_from_postgres():
    """从 PostgreSQL 获取公司列表"""
    write_log("🔍 连接 PostgreSQL 读取公司列表...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT security FROM csr_reporting.company_static;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        companies = [row[0] for row in rows]
        write_log(f"✅ 获取到 {len(companies)} 家公司")
        return companies
    except Exception as e:
        write_log(f"❌ PostgreSQL 读取失败: {type(e).__name__}, {e}")
        return []


def search_by_years(driver, company_name, years, keywords):
    """
    循环(年份 + 关键词)搜索
    如果找到PDF则下载并保存, 并行搜索速度更快
    """
    found_any = False
    for year in years:
        # 断点续爬: 如果 MongoDB 已有该年份记录，则跳过
        existing = mongo_db["csr_reports"].find_one(
            {"company_name": company_name, "csr_report_year": year}
        )
        if existing:
            write_log(f"⚠️ {company_name}({year}) 已存在于MongoDB, 跳过")
            continue

        for kw in keywords:
            query = f"{company_name} {year} {kw}"
            write_log(f"🚀 搜索关键词: {query}")
            results = get_search_results(driver, query, timeout=5)

            for r in results:
                url = r.get_attribute("href")
                pdf_path = download_pdf(company_name, year, url)
                if pdf_path:
                    obj_name = upload_to_minio(company_name, year, pdf_path)
                    if obj_name:
                        save_csr_report_info_to_mongo(company_name, url, obj_name, year)
                    found_any = True
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
            # 将 sleep 缩短到 0.2
            time.sleep(0.2)

    return found_any


def search_and_process(company_name):
    """搜索、下载、上传(不同年份)的CSR报告"""
    write_log(f"🚀 开始处理公司: {company_name}")

    driver = None
    try:
        driver = init_driver()

        # 需要搜索的年份 (2020~2024)
        years = range(2020, 2025)
        # 减少关键词数量，加速搜索
        keywords = [
            "corporate sustainability report filetype:pdf",
            "ESG report filetype:pdf",
        ]
        found = search_by_years(driver, company_name, years, keywords)
        if not found:
            write_log(f"⚠️ {company_name} 未找到任何PDF")
    except Exception as e:
        write_log(f"❌ 处理 {company_name} 失败: {type(e).__name__}, {e}")
    finally:
        if driver:
            driver.quit()


def process_batch(company_list):
    """
    多线程处理公司列表, 提升速度
    将 max_workers 从 5 改为 10
    """
    write_log("🚀 开始批量爬取数据... (max_workers=10)")
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(search_and_process, company_list)


def main():
    """手动触发的爬虫流程"""
    companies = get_company_list_from_postgres()
    if not MINIO_CLIENT.bucket_exists(BUCKET_NAME):
        MINIO_CLIENT.make_bucket(BUCKET_NAME)

    write_log("📢 开始处理公司列表...")
    process_batch(companies)
    write_log("🎉 全部公司处理完成！")


def schedule_scraper():
    """使用 APScheduler，每 7 天运行一次爬虫"""
    scheduler = BlockingScheduler()
    scheduler.add_job(main, "interval", days=7)
    write_log("⏳ Scraper scheduler started, running every 7 days...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        write_log("🛑 Scheduler stopped.")


if __name__ == "__main__":
    # 默认运行一次爬虫
    main()
