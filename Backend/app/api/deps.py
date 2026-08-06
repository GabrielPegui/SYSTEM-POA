"""Shared FastAPI dependencies (dependency injection entry points)."""

from app.database.session import get_db

__all__ = ["get_db"]
