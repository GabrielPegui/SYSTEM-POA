"""Microsoft SQL Server session management.

The engine is created lazily so the application can start even when the
database is not configured or unavailable (e.g. local development without
SQL Server). The schema is defined by the SQLAlchemy models in
``app.infrastructure.persistence.models`` and applied through the versioned
migrations under ``app/database/migrations`` (see ADR-003).
"""

from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine | None:
    """Create and cache the SQLAlchemy engine from the configured URL."""
    global _engine, _session_factory

    if _engine is not None:
        return _engine

    if not settings.database_url:
        logger.warning("DATABASE_URL is not configured. Database access is disabled.")
        return None

    try:
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"timeout": 5},
        )
        _session_factory = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    except (ImportError, ModuleNotFoundError) as exc:
        logger.error("Database driver not installed for DATABASE_URL: %s", exc)
        _engine = None
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to initialize database engine: %s", exc)
        _engine = None

    return _engine


def session_factory() -> sessionmaker[Session] | None:
    """Return the cached session factory, creating the engine if needed."""
    get_engine()
    return _session_factory


def get_db():
    """FastAPI dependency that yields a database session when configured.

    Yields ``None`` when the database is not configured so endpoints can
    degrade gracefully during development.
    """
    factory = session_factory()
    if factory is None:
        yield None
        return

    db: Session = factory()
    try:
        yield db
    finally:
        db.close()


def database_status() -> dict[str, Any]:
    """Non-blocking status of the database configuration.

    It intentionally does not open a connection so the health endpoint
    remains responsive when SQL Server is down.
    """
    if not settings.database_url:
        return {"configured": False, "detail": "DATABASE_URL not configured"}
    return {"configured": True, "detail": "engine initialized on first use"}
