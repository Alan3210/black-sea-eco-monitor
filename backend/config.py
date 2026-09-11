import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    PROJECT_NAME = os.getenv(
        "PROJECT_NAME",
        "Black Sea Eco Monitor"
    )


    ENVIRONMENT = os.getenv(
        "ENVIRONMENT",
        "development"
    )

    NEWS_RSS_URL = os.getenv(
    "NEWS_RSS_URL",
    ""
)

    NEWS_SOURCE_NAME = os.getenv(
        "NEWS_SOURCE_NAME",
        "Black Sea News Feed"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./eco_monitor.db"
    )


    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )


settings = Settings()