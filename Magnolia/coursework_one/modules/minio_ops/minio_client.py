import os
import yaml
import io  # 需要导入 io 处理二进制流
from minio import Minio
from minio.error import S3Error


def load_config():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    conf_path = os.path.join(base_dir, "..", "..", "config", "conf.yaml")
    with open(conf_path, "r") as f:
        return yaml.safe_load(f)


def get_minio_client():
    """初始化 MinIO 客户端"""
    config = load_config()
    minio_conf = config["minio"]
    client = Minio(
        minio_conf["endpoint"],
        access_key=minio_conf["access_key"],
        secret_key=minio_conf["secret_key"],
        secure=minio_conf["secure"],
    )
    return client


def upload_to_minio(bucket_name, object_name, file_bytes):
    """
    上传文件到 MinIO

    :param bucket_name: MinIO 存储桶 (str)
    :param object_name: 存储路径 (str) 例如: "Apple/2024/CSR_Report.pdf"
    :param file_bytes: 文件二进制内容 (bytes)
    :return: MinIO 访问路径 (str)
    """
    client = get_minio_client()

    # 确保 Bucket 存在
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    # 把 `file_bytes` 变成文件流
    file_stream = io.BytesIO(file_bytes)

    # 上传到 MinIO
    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=file_stream,  # 这里用 BytesIO 作为文件流
        length=len(file_bytes),
        content_type="application/pdf",
    )

    print(f"✅ 文件上传成功: {bucket_name}/{object_name}")
    return f"{bucket_name}/{object_name}"
