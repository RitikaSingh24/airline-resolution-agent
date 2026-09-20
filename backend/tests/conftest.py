"""
Pytest fixtures for the database test suite.

Each test gets its own isolated, in-memory SQLite database so tests
never pollute the real development database.
"""
import os
import sys

# Ensure src directory is in Python path for test execution
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import Base so create_all sees the metadata
from db.base import Base

# Import all models to register them with Base.metadata before create_all.
import models.customer      # noqa: F401
import models.booking       # noqa: F401
import models.conversation  # noqa: F401
import models.message       # noqa: F401
import models.action        # noqa: F401
import models.escalation    # noqa: F401


from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db() -> Session:
    """
    Provide a fresh SQLAlchemy session backed by an in-memory SQLite database.

    The database is created at the start of each test function and discarded
    at the end, ensuring full isolation between tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture(scope="function")
def client(db: Session):
    """Provides a FastAPI TestClient using the isolated in-memory test database session."""
    from db.seed import seed_data
    from db.session import get_db
    from main import app
    from fastapi.testclient import TestClient

    seed_data(db)

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def default_test_env(monkeypatch):
    """Ensures test suite runs deterministically without hitting live LLM provider APIs."""
    from core.config import settings
    monkeypatch.setattr(settings, "LLM_API_KEY", None)

