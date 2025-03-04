import psycopg2
from kafka import KafkaProducer
import json

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'csr-report'

# PostgreSQL configuration
PG_HOST = 'host.docker.internal'
PG_PORT = 5439
PG_DB = 'fift'
PG_USER = 'postgres'
PG_PASSWORD = 'postgres'

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Connect to PostgreSQL
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

# Fetch report URL data from PostgreSQL
def fetch_report_data(conn):
    print("Fetching report data from PostgreSQL...")
    try:
        cursor = conn.cursor()
        # Query company_reports and company_static tables to get company_name and report_url
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

# Group report URLs by company name
def group_reports_by_company(reports):
    grouped_data = {}
    for company_name, security, report_url in reports:
        if company_name not in grouped_data:
            grouped_data[company_name] = []
        grouped_data[company_name].append(report_url)
    return grouped_data

# Send message to Kafka
def send_to_kafka(company_name, report_urls):
    message = {
        'company_name': company_name,
        'report_urls': report_urls
    }
    print(f"Sending message to Kafka: {message}")
    producer.send(KAFKA_TOPIC, value=message)
    producer.flush()
    print("Message sent successfully!")

# Main logic
def main():
    # Connect to PostgreSQL
    conn = connect_to_postgres()

    # Fetch report URL data from PostgreSQL
    reports = fetch_report_data(conn)

    # Group report URLs by company name
    grouped_reports = group_reports_by_company(reports)

    # Iterate through grouped data and send to Kafka
    for company_name, report_urls in grouped_reports.items():
        print(f"\nProcessing reports for company: {company_name}")
        send_to_kafka(company_name, report_urls)

    # Close PostgreSQL connection
    conn.close()
    print("\nAll messages sent to Kafka!")

if __name__ == "__main__":
    main()
