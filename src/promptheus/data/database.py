"""Database configuration and session management."""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from promptheus.config import get_settings

Base = declarative_base()

settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.environment == "development",
)

# Async engine for new async repositories
async_engine = create_async_engine(
    settings.database_url.replace("sqlite://", "sqlite+aiosqlite://")
    if "sqlite" in settings.database_url
    else settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    if "postgresql" in settings.database_url
    else settings.database_url,
    echo=settings.environment == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session (sync - for backward compatibility)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async_db = AsyncSessionLocal()
    try:
        yield async_db
        await async_db.commit()
    except Exception:
        await async_db.rollback()
        raise
    finally:
        await async_db.close()
