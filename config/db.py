from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
# loaded manually due to subdirectory structure of this project
#       (config dict unable to locate .env file)
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Explicitly set the .env path
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

print(f"✅ Loaded .env from: {dotenv_path}")  # Debugging

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
        env_file=dotenv_path,  # Explicitly point to .env
        env_file_encoding="utf-8",
        env_prefix="",  # Remove "DB_" prefix if it's causing issues
        case_sensitive=True,
        extra="ignore",
    )

database_settings = DataBaseSettings()

# Debugging: Print one variable to verify it's loaded
print(f"🔍 POSTGRES_USERNAME = {database_settings.POSTGRES_USERNAME}")
