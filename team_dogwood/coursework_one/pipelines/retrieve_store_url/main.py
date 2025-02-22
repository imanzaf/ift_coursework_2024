import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config.minio import minio_settings  # noqa: E402

if __name__ == "__main__":
    print(minio_settings.USERNAME)
