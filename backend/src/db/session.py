"""
Database session management.

Reads DATABASE_URL from the environment (falls back to a local SQLite path).
Automatically creates the parent directory for SQLite databases.
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/airline_resolution.db",
)

# For SQLite, ensure the parent directory exists before the engine is created.
if DATABASE_URL.startswith("sqlite:///"):
    # Strip the leading "sqlite:///" prefix and resolve relative path.
    raw_path = DATABASE_URL[len("sqlite:///"):]
    db_path = Path(raw_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

# connect_args required for SQLite to allow multi-threaded access (e.g. tests).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def get_db():
    """
    Generator that yields a database session and closes it afterwards.

    Usage (plain Python):
        with get_db() as db:
            ...

    Usage (FastAPI dependency injection – future API layer):
        db: Session = Depends(get_db)
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
