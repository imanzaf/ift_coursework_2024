# analysis_pipeline.py
import os
import io
from pymongo import MongoClient
from minio import Minio
import pdfplumber
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# nltk.download('vader_lexicon')  # 只需第一次下载

# 示例关键词提取库，比如 Rake 或 yake
# pip install python-rake
# pip install yake
import yake

MONGO_URI = "mongodb://localhost:27019"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["csr_db"]
collection = mongo_db["csr_reports"]

MINIO_CLIENT = Minio(
    "localhost:9000",
    access_key="ift_bigdata",
    secret_key="minio_password",
    secure=False,
)
BUCKET_NAME = "csr-reports"


def extract_text_from_pdf(pdf_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def sentiment_analysis(text):
    sia = SentimentIntensityAnalyzer()
    scores = sia.polarity_scores(text)
    return scores["compound"]  # 返回整体情感分数


def keyword_extraction(text, max_k=5):
    kw_extractor = yake.KeywordExtractor(n=1, top=max_k)
    keywords = kw_extractor.extract_keywords(text)
    # keywords 结构: [(词, 分数), (词, 分数), ...]
    # 你可以根据分数过滤或直接返回
    return [k[0] for k in keywords]


def run_analysis():
    docs = list(collection.find())
    for doc in docs:
        path = doc.get("storage_path")
        if not path:
            continue

        # 从 MinIO 下载 PDF
        try:
            data = MINIO_CLIENT.get_object(BUCKET_NAME, path)
            pdf_bytes = data.read()
            data.close()
        except Exception as e:
            print(f"❌ Failed to download {path}: {e}")
            continue

        # 提取文本
        text = extract_text_from_pdf(pdf_bytes)
        if not text:
            print(f"⚠️ No text extracted from {path}")
            continue

        # 情感分析
        sentiment_score = sentiment_analysis(text)
        # 关键词提取
        keywords = keyword_extraction(text, max_k=5)

        # 将结果写入 MongoDB
        collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "analysis.sentiment_score": sentiment_score,
                    "analysis.keywords": keywords,
                }
            },
        )
        print(
            f"✅ {doc['company_name']} ({doc['csr_report_year']}) -> sentiment: {sentiment_score}, keywords: {keywords}"
        )


if __name__ == "__main__":
    run_analysis()
