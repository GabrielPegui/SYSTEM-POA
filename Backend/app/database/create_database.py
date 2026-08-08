"""Create the configured database if it does not exist.

Idempotent bootstrap step used before running Alembic migrations:

    python -m app.database.create_database
    alembic upgrade head

The database name is taken from ``DATABASE_URL``; the connection is made
against the ``master`` database of the same SQL Server instance because the
target database may not exist yet.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_database() -> str:
    """Create the configured database (no-op when it already exists)."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    url = make_url(settings.database_url)
    database = url.database
    if not database:
        raise RuntimeError("DATABASE_URL must include a database name")

    admin_url = url.set(database="master")
    engine = create_engine(
        admin_url,
        connect_args={"timeout": 5},
        isolation_level="AUTOCOMMIT",
    )
    try:
        with engine.connect() as connection:
            connection.execute(
                text(f"IF DB_ID(N'{database}') IS NULL EXEC(N'CREATE DATABASE [{database}]')")
            )
    finally:
        engine.dispose()

    logger.info("Database '%s' is ready.", database)
    return database


if __name__ == "__main__":
    create_database()
