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

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./eco_monitor.db"
    )

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )

    NEWS_RSS_URL = os.getenv(
        "NEWS_RSS_URL",
        ""
    )

    NEWS_SOURCE_NAME = os.getenv(
        "NEWS_SOURCE_NAME",
        "Black Sea News Feed"
    )

    NEWS_MAX_AGE_DAYS = int(
        os.getenv(
            "NEWS_MAX_AGE_DAYS",
            "7"
        )
    )

    OLLAMA_BASE_URL = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )

    OLLAMA_MODEL = os.getenv(
        "OLLAMA_MODEL",
        "qwen3.5:9b"
    )


settings = Settings()