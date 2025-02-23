import psycopg2
from kafka import KafkaProducer
import json

# Kafka 配置
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'csr-report'

# PostgreSQL 配置
PG_HOST = 'host.docker.internal'
PG_PORT = 5439
PG_DB = 'fift'
PG_USER = 'postgres'
PG_PASSWORD = 'postgres'

# 初始化 Kafka 生产者
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# 连接到 PostgreSQL
def connect_to_postgres():
    print("Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        print("Successfully connected to PostgreSQL!")
        return conn
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        raise

# 从 PostgreSQL 读取报告 URL 数据
def fetch_report_data(conn):
    print("Fetching report data from PostgreSQL...")
    try:
        cursor = conn.cursor()
        # 查询 company_reports 表和 company_static 表，获取 company_name 和 report_url
        cursor.execute("""
            SELECT cs.security, cs.security, cr.report_url
            FROM csr_reporting.company_reports cr
            JOIN csr_reporting.company_static cs ON cr.security = cs.security
        """)
        reports = cursor.fetchall()
        print("Report data fetched successfully!")
        return reports
    except Exception as e:
        print(f"Failed to fetch report data: {e}")
        raise

# 按公司名称分组报告 URL
def group_reports_by_company(reports):
    grouped_data = {}
    for company_name, security, report_url in reports:
        if company_name not in grouped_data:
            grouped_data[company_name] = []
        grouped_data[company_name].append(report_url)
    return grouped_data

# 发送消息到 Kafka
def send_to_kafka(company_name, report_urls):
    message = {
        'company_name': company_name,
        'report_urls': report_urls
    }
    print(f"Sending message to Kafka: {message}")
    producer.send(KAFKA_TOPIC, value=message)
    producer.flush()
    print("Message sent successfully!")

# 主逻辑
def main():
    # 连接到 PostgreSQL
    conn = connect_to_postgres()

    # 从 PostgreSQL 读取报告 URL 数据
    reports = fetch_report_data(conn)

    # 按公司名称分组报告 URL
    grouped_reports = group_reports_by_company(reports)

    # 遍历分组数据并发送到 Kafka
    for company_name, report_urls in grouped_reports.items():
        print(f"\nProcessing reports for company: {company_name}")
        send_to_kafka(company_name, report_urls)

    # 关闭 PostgreSQL 连接
    conn.close()
    print("\nAll messages sent to Kafka!")

if __name__ == "__main__":
    main()
