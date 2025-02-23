import json
from kafka import KafkaProducer

# Kafka 配置
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'csr-report'

# 初始化 Kafka 生产者
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

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

# 测试数据
if __name__ == "__main__":
    test_data = {
        "company_name": "Example Corp",
        "report_urls": [
            "http://example.com/report1.pdf",
            "http://example.com/report2.pdf"
        ]
    }
    send_to_kafka(test_data["company_name"], test_data["report_urls"])
