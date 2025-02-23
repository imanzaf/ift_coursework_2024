import json
import logging
import os
import sqlite3
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


# 自定义缓存实现
class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


# 设置基础URL
BASE_URL = "https://www.responsibilityreports.com"


# 创建带有重试策略的Session
def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session


session = create_session()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google 搜索配置
GOOGLE_API_KEY = "AIzaSyA3VVtTUL8ZsXCyu_es-_V4fHLHtx1cSvE"
GOOGLE_CSE_ID = "55adbcac3c4f44f3a"

# 结果保存路径
RESULTS_FILE = "company_pdf_links.json"


def create_google_service():
    """创建Google搜索服务"""
    service = build(
        "customsearch",
        "v1",
        developerKey=GOOGLE_API_KEY,
        cache=MemoryCache()
    )
    return service


def read_companies_from_db(db_path):
    """从数据库获取列表"""
    conn = None
    try:
        db_path = Path(db_path)
        if not db_path.exists():
            logger.error(f"数据库文件不存在：{db_path.resolve()}")
            return []
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='equity_static'
        """)
        if not cursor.fetchone():
            logger.error("equity_static表不存在")
            return []
        cursor.execute("SELECT security FROM equity_static")
        companies = [row[0] for row in cursor.fetchall()]
        logger.info(f"从数据库成功读取 {len(companies)} 家公司")
        return companies
    except Exception as e:
        logger.error(f"数据库读取错误: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()


def format_company_name(company_name, use_corporation=False):
    """格式化公司名称，可选择将company替换为corporation"""
    clean_name = company_name.lower()
    
    # 先处理corp的情况
    clean_name = clean_name.replace("corp.", "corporation")  # 处理带点的情况
    clean_name = clean_name.replace("corp ", "corporation ")  # 处理带空格的情况
    clean_name = clean_name.replace("corp-", "corporation-")  # 处理带连字符的情况
    
    # 如果启用corporation替换
    if use_corporation:
        clean_name = clean_name.replace("company", "corporation")
    
    # 最后处理空格和点
    clean_name = clean_name.replace(" ", "-")
    clean_name = clean_name.replace(".", "")
    
    return clean_name


def try_website_search(company_name, use_corporation=False):
    """尝试在网站上搜索PDF链接"""
    formatted_name = format_company_name(company_name, use_corporation)
    search_url = f"{BASE_URL}/Company/{formatted_name}"
    logger.info(f"尝试访问URL: {search_url}")

    try:
        response = session.get(search_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links_set = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.lower().endswith('.pdf'):
                full_url = BASE_URL + href if not href.startswith('http') else href
                full_url = full_url.strip().rstrip('/')
                pdf_links_set.add(full_url)

        if pdf_links_set:
            logger.info(
                f"使用{'corporation' if use_corporation else 'company'}在网站上找到 {len(pdf_links_set)} 个PDF链接")
            return list(pdf_links_set)
        return None

    except Exception as e:
        logger.error(f"网站搜索失败 ({'corporation' if use_corporation else 'company'}): {str(e)}")
        return None


def is_valid_pdf_link(link, title=""):
    """检查PDF链接是否有效（不包含annual/Annual）"""
    link_lower = link.lower()
    title_lower = title.lower()
    
    # 检查URL和标题中是否包含"annual"
    if "annual" in link_lower or "annual" in title_lower:
        logger.info(f"跳过annual报告: {link}")
        return False
    return True


def google_search_pdf(company_name):
    """使用Google API搜索PDF文件，过滤掉annual报告"""
    pdf_links_set = set()

    try:
        service = create_google_service()

        # 只搜索最近的年份以节省配额
        for year in range(2013, 2024):
            query = f"{company_name} {year} responsibility report sustainability report filetype:pdf"
            logger.info(f"执行Google搜索: {query}")

            try:
                result = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=10).execute()

                if "items" in result:
                    for item in result["items"]:
                        link = item["link"].strip().rstrip('/')
                        title = item.get("title", "")  # 获取搜索结果的标题
                        
                        if link.lower().endswith('.pdf') and is_valid_pdf_link(link, title):
                            pdf_links_set.add(link)
                            # 每年只获取一个有效的PDF链接
                            break

                time.sleep(1)  # 避免触发API限制

            except Exception as e:
                logger.error(f"年份 {year} 的Google搜索失败: {str(e)}")
                # 如果遇到配额限制，立即停止搜索
                if "Quota exceeded" in str(e):
                    logger.error("Google API配额已超限，停止搜索")
                    break

    except Exception as e:
        logger.error(f"Google搜索服务创建失败: {str(e)}")

    return list(pdf_links_set)


def get_pdf_links_for_company(company_name):
    """获取公司的所有PDF链接，使用多种搜索策略"""
    logger.info(f"开始处理公司: {company_name}")

    # 策略1：使用原始公司名称在网站搜索
    pdf_links = try_website_search(company_name, use_corporation=False)
    if pdf_links:
        return pdf_links

    # 策略2：将company替换为corporation后在网站搜索
    if "company" in company_name.lower():
        logger.info("尝试将'company'替换为'corporation'后搜索")
        pdf_links = try_website_search(company_name, use_corporation=True)
        if pdf_links:
            return pdf_links

    # 策略3：使用Google API搜索
    logger.info("网站搜索未找到结果，尝试使用Google API搜索")
    pdf_links = google_search_pdf(company_name)

    return pdf_links


def save_results_to_json(results):
    """将结果保存为JSON文件"""
    try:
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        logger.info(f"结果已保存到 {RESULTS_FILE}")
    except Exception as e:
        logger.error(f"保存JSON失败: {str(e)}")


def load_existing_results():
    """加载现有的结果文件"""
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载现有结果失败: {str(e)}")
    return {}


def main():
    # 设置数据库路径
    # 获取脚本文件的绝对路径
    script_dir = Path(__file__).resolve().parent
    # 构建数据文件的路径
    db_path = script_dir / "../../../000.Database/SQL/Equity.db"
    # 解析路径（去除多余的 ../）
    db_path = db_path.resolve()

    # 读取公司列表
    companies = read_companies_from_db(db_path)
    if not companies:
        logger.error("未能获取公司列表")
        return

    logger.info(f"共获取到 {len(companies)} 家公司")

    # 加载现有结果
    results = load_existing_results()

    # 处理每个公司
    for i, company in enumerate(companies, 1):
        logger.info(f"[{i}/{len(companies)}] 正在处理: {company}")

        # 如果公司已经处理过，跳过
        if company in results:
            logger.info(f"{company} 已经处理过，跳过")
            continue

        # 获取PDF链接
        pdf_links = get_pdf_links_for_company(company)

        # 保存结果
        results[company] = pdf_links

        # 每处理一家公司保存一次结果
        if i % 1 == 0:
            save_results_to_json(results)

        # 避免请求过于频繁
        time.sleep(1)

    # 最终保存结果
    save_results_to_json(results)
    logger.info("所有公司处理完成")


if __name__ == "__main__":
    main()