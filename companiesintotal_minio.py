from minio import Minio

# 连接 MinIO
client = Minio(
    "localhost:9000",
    access_key="ift_bigdata",
    secret_key="minio_password",
    secure=False
)

# 列出对象
objects = client.list_objects("csreport", recursive=True)

# 提取公司名（假设文件名格式：公司名_年份.pdf）
companies = set()
for obj in objects:
    filename = obj.object_name
    company_name = filename.split('_')[0]  # 获取公司名
    companies.add(company_name)

print(f"爬取的公司总数: {len(companies)}")
