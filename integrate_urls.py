import json
import psycopg2
import re

# JSON 文件路径
json_file_path = "data.json"

# 读取 JSON 文件
with open(json_file_path, "r") as file:
    data = json.load(file)

# PostgreSQL 数据库连接配置
db_config = {
    "dbname": "fift",
    "user": "postgres",
    "password": "postgres",
    "host": "host.docker.internal",
    "port": 5439
}

# 连接 PostgreSQL 数据库
try:
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # 遍历 JSON 数据
    for company_name, urls in data.items():
        # 检查公司名称是否存在于 company_static 表中
        cursor.execute("SELECT security FROM csr_reporting.company_static WHERE security = %s", (company_name,))
        result = cursor.fetchone()

        if result:
            # 如果公司存在，插入 URL 数据
            for url in urls:
                # 从 URL 中提取年份
                year_match = re.search(r"(\d{4})\.pdf$", url)
                report_year = int(year_match.group(1)) if year_match else None

                # 插入数据到 company_reports 表
                insert_query = """
                    INSERT INTO csr_reporting.company_reports (security, report_url, report_year)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (company_name, url, report_year))

    # 提交事务
    conn.commit()
    print("数据插入成功！")

except Exception as e:
    print(f"发生错误：{e}")
finally:
    # 关闭数据库连接
    if conn:
        cursor.close()
        conn.close()
