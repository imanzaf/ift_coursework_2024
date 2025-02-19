from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
# loaded manually due to subdirectory structure of this project
#       (config dict unable to locate .env file)
load_dotenv()


class AuthSettings(BaseSettings):
    MINIO_USERNAME: str
    MINIO_PASSWORD: str
    MINIO_PORT: str

    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: str

    GOOGLE_API_KEY: str
    GOOGLE_ENGINE_ID: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "AUTH_"
        case_sensitive = True
        extra = "ignore"


auth_settings = AuthSettings()
