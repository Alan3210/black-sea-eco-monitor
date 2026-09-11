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


settings = Settings()