from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
# loaded manually due to subdirectory structure of this project
#       (config dict unable to locate .env file)
load_dotenv()


class SearchSettings(BaseSettings):
    """Configuration for search settings, including Google API and sustainability reports API.

    This class defines the configuration settings required to interact with the Google Custom Search API
    and a sustainability reports API. The settings are loaded from environment variables or a `.env` file.

    Attributes:
        GOOGLE_API_URL (str): The base URL for the Google Custom Search API.
        GOOGLE_API_KEY (str): The API key for the Google Custom Search API.
        GOOGLE_ENGINE_ID (str): The search engine ID for the Google Custom Search API.
        SUSTAINABILITY_REPORTS_API_URL (str): The base URL for the sustainability reports API.

    Example:
        >>> search_settings = SearchSettings()
        >>> print(search_settings.GOOGLE_API_URL)
        https://www.googleapis.com/customsearch/v1
    """

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
