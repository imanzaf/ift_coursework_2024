from pymongo import MongoClient  # ✅ 确保导入 MongoClient

# 连接 MongoDB
MONGO_URI = "mongodb://localhost:27019"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["csr_db"]
collection_reports = mongo_db["csr_reports"]

# ✅ 创建索引，提高查询性能
collection_reports.create_index(
    [("company_name", 1), ("csr_report_year", 1)]
)  # 复合索引
collection_reports.create_index([("csr_report_year", 1)])  # 年份单独索引
collection_reports.create_index([("company_name", "text")])  # 文本索引（用于模糊搜索）

print("✅ MongoDB 索引创建成功")

# ✅ 显示索引信息，确认索引是否正确创建
indexes = collection_reports.index_information()
print("✅ 当前索引：", indexes)
