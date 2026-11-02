"""Main application entry point for Ingestion Service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from atlas_observability import CorrelationIdMiddleware, setup_logging
from fastapi import FastAPI

from ingestion_service.api.health import router as health_router
from ingestion_service.core.config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle events: startup and shutdown."""
    settings = get_settings()
    logger = setup_logging(
        service_name=settings.service_name,
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    logger.info(
        "Service '%s' starting up (version=%s, env=%s, port=%d)",
        settings.service_name,
        settings.service_version,
        settings.environment,
        settings.port,
    )
    yield
    logger.info("Service '%s' shutting down gracefully", settings.service_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    """FastAPI application factory for Ingestion Service."""
    current_settings = settings or get_settings()

    app = FastAPI(
        title="ATLAS Ingestion Service",
        description="Document extraction, normalization, and chunking service for ATLAS",
        version=current_settings.service_version,
        lifespan=lifespan,
    )

    if settings is not None:
        app.dependency_overrides[get_settings] = lambda: current_settings

    # Cross-cutting middleware
    app.add_middleware(CorrelationIdMiddleware)

    # Routes
    app.include_router(health_router)
    from ingestion_service.api.documents import router as documents_router

    app.include_router(documents_router)

    @app.get("/", tags=["Root"])
    async def root_identity() -> dict[str, str]:
        return {
            "service": current_settings.service_name,
            "version": current_settings.service_version,
            "status": "running",
        }

    return app


app = create_app()
