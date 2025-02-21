from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
# loaded manually due to subdirectory structure of this project
#       (config dict unable to locate .env file)
load_dotenv()


class GoogleSettings(BaseSettings):
    API_KEY: str
    ENGINE_ID: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "GOOGLE_"
        case_sensitive = True
        extra = "ignore"


google_settings = GoogleSettings()
