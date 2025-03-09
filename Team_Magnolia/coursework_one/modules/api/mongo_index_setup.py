from pymongo import MongoClient  # ✅ Ensure MongoClient is imported

# Connect to MongoDB
MONGO_URI = "mongodb://localhost:27019"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["csr_db"]
collection_reports = mongo_db["csr_reports"]

# ✅ Create indexes to improve query performance
collection_reports.create_index(
    [("company_name", 1), ("csr_report_year", 1)]
)  # Compound index
collection_reports.create_index([("csr_report_year", 1)])  # Index for year
collection_reports.create_index([("company_name", "text")])  # Text index (for fuzzy search)

print("✅ MongoDB indexes created successfully")

# ✅ Display index information to confirm proper creation
indexes = collection_reports.index_information()
print("✅ Current indexes:", indexes)
