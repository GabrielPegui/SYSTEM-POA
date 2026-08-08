"""Declarative base for the SQLAlchemy models.

The naming convention guarantees deterministic constraint and index names
across both ``metadata.create_all`` (used by tests) and the versioned
Alembic migrations (used in real environments), which keeps the schema
reproducible (ADR-001, ADR-003).
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all database models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
