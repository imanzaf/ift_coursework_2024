#!/bin/bash

# 设置 Python 虚拟环境（如果适用）
source .venv/bin/activate

# 检查 MongoDB 是否启动
echo "🔍 Checking MongoDB status..."
until nc -z localhost 27019; do
  echo "⏳ Waiting for MongoDB to be ready..."
  sleep 2
done
echo "✅ MongoDB is up and running!"

# 检查 MinIO 是否启动
echo "🔍 Checking MinIO status..."
until curl --output /dev/null --silent --head --fail http://localhost:9000/minio/health/live; do
  echo "⏳ Waiting for MinIO to be ready..."
  sleep 2
done
echo "✅ MinIO is up and running!"

# 启动 FastAPI 服务器
echo "🚀 Starting FastAPI API..."
uvicorn modules.api.fastapi_api:app --host 0.0.0.0 --port 8000 --reload > logs/api.log 2>&1 &

# 确保 FastAPI 启动成功
sleep 3
if nc -z localhost 8000; then
  echo "✅ FastAPI API is running at http://localhost:8000"
else
  echo "❌ FastAPI failed to start. Check logs/api.log for details."
fi
