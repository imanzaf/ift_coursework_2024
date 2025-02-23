from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
# loaded manually due to subdirectory structure of this project
#       (config dict unable to locate .env file)
load_dotenv()


class DataBaseSettings(BaseSettings):
    POSTGRES_DRIVER: str
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: str
    POSTGRES_HOST: str
    POSTGRES_DB_NAME: str

    MINIO_USERNAME: str
    MINIO_PASSWORD: str
    MINIO_HOST: str
    MINIO_PORT: str
    MINIO_BUCKET_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DB_",
        case_sensitive=True,
        extra="ignore",
    )


database_settings = DataBaseSettings()
