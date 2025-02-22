from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
# loaded manually due to subdirectory structure of this project
#       (config dict unable to locate .env file)
load_dotenv()


class SearchSettings(BaseSettings):
    GOOGLE_API_URL: str
    GOOGLE_API_KEY: str
    GOOGLE_ENGINE_ID: str

    SUSTAINABILITY_REPORTS_API_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SEARCH_",
        case_sensitive=True,
        extra="ignore",
    )


search_settings = SearchSettings()
