from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
# loaded manually due to subdirectory structure of this project
#       (config dict unable to locate .env file)
load_dotenv()


class MinioSettings(BaseSettings):
    USERNAME: str
    PASSWORD: str
    PORT: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "MINIO_"
        case_sensitive = True
        extra = "ignore"


minio_settings = MinioSettings()
