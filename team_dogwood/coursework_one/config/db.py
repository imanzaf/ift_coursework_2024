from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
# loaded manually due to subdirectory structure of this project
#       (config dict unable to locate .env file)
load_dotenv()


class DataBaseSettings(BaseSettings):
    """Configuration for database settings, including PostgreSQL and MinIO.

    This class defines the configuration settings required to connect to a PostgreSQL database
    and a MinIO storage service. The settings are loaded from environment variables or a `.env` file.

    Attributes:
        POSTGRES_DRIVER (str): The driver used to connect to the PostgreSQL database.
        POSTGRES_USERNAME (str): The username for the PostgreSQL database.
        POSTGRES_PASSWORD (str): The password for the PostgreSQL database.
        POSTGRES_PORT (str): The port on which the PostgreSQL database is running.
        POSTGRES_HOST (str): The host address of the PostgreSQL database.
        POSTGRES_DB_NAME (str): The name of the PostgreSQL database.
        MINIO_USERNAME (str): The username for the MinIO storage service.
        MINIO_PASSWORD (str): The password for the MinIO storage service.
        MINIO_PORT (str): The port on which the MinIO service is running.
        MINIO_BUCKET_NAME (str): The name of the bucket in MinIO where files are stored.

    Example:
        >>> database_settings = DataBaseSettings()
        >>> print(database_settings.POSTGRES_HOST)
        localhost
    """

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
