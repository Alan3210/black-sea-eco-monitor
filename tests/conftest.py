from pathlib import Path

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from backend.main import app
from backend.database.database import Base, get_db


TEST_RESULTS_DIR = Path("test-results")
TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TEST_DATABASE_PATH = TEST_RESULTS_DIR / "test_database.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DATABASE_PATH.as_posix()}"


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(autouse=True)
def setup_database():

    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )


def override_get_db():

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():

    return TestClient(app)
