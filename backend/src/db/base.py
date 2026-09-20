"""
Declarative base shared by all SQLAlchemy models.

Import this module to get `Base`, then import all model modules
before calling Base.metadata.create_all().
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass
