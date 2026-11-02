"""Database session and engine lifecycle management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from research_orchestrator.core.config import get_settings


def create_engine_and_sessionmaker(
    database_url: str | None = None,
    echo: bool = False,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create configured AsyncEngine and sessionmaker factory."""
    settings = get_settings()
    url = database_url or settings.database_url

    engine_kwargs: dict = {"echo": echo or settings.db_echo}
    if not url.startswith("sqlite"):
        engine_kwargs["pool_size"] = settings.db_pool_size
        engine_kwargs["max_overflow"] = settings.db_max_overflow

    engine = create_async_engine(url, **engine_kwargs)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return engine, session_factory


# Module-level singletons for standard runtime
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the global async engine singleton."""
    global _engine, _session_factory
    if _engine is None:
        _engine, _session_factory = create_engine_and_sessionmaker()
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the global async sessionmaker singleton."""
    global _engine, _session_factory
    if _session_factory is None:
        _engine, _session_factory = create_engine_and_sessionmaker()
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def scoped_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for background tasks and tests requiring an async session."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
