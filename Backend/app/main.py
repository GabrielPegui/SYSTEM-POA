"""Application entry point (FastAPI application factory)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes.health import router as health_router
from app.api.routes.orders import router as orders_router
from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import get_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifecycle hooks executed on application startup and shutdown."""
    logger.info(
        "Starting %s v%s (%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    engine = get_engine()
    if engine is not None:
        try:
            from app.database.base import Base
            from app.infrastructure.persistence import models  # noqa: F401
            Base.metadata.create_all(engine)
        except Exception as exc:
            logger.warning("Auto table creation skipped: %s", exc)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)
    application.include_router(health_router, tags=["health"])
    application.include_router(orders_router, tags=["orders"])
    return application


app = create_app()
