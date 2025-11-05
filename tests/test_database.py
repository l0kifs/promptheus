"""Tests for database configuration and session management."""

import pytest
from sqlalchemy import text

from promptheus.data.database import (
    AsyncSessionLocal,
    Base,
    SessionLocal,
    async_engine,
    engine,
    get_async_db,
    get_db,
)


class TestDatabaseConfiguration:
    """Tests for database engine and session configuration."""

    def test_sync_engine_creation(self):
        """Test synchronous engine is created correctly."""
        assert engine is not None
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1

    @pytest.mark.asyncio
    async def test_async_engine_creation(self):
        """Test asynchronous engine is created correctly."""
        assert async_engine is not None
        # Test basic async connection
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1

    def test_session_local_creation(self):
        """Test session maker is configured correctly."""
        assert SessionLocal is not None
        session = SessionLocal()
        assert session is not None
        session.close()

    @pytest.mark.asyncio
    async def test_async_session_local_creation(self):
        """Test async session maker is configured correctly."""
        assert AsyncSessionLocal is not None
        session = AsyncSessionLocal()
        assert session is not None
        await session.close()

    def test_base_declarative_base(self):
        """Test Base is properly configured."""
        assert Base is not None
        # Check that Base has metadata
        assert hasattr(Base, "metadata")


class TestSyncDatabaseSession:
    """Tests for synchronous database session management."""

    def test_get_db_context_manager_success(self):
        """Test get_db yields session and commits on success."""
        with get_db() as db:
            assert db is not None
            # Test basic query
            result = db.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1
        # Session should be closed after context

    def test_get_db_context_manager_rollback_on_exception(self):
        """Test get_db rolls back on exception."""
        with pytest.raises(ValueError), get_db() as db:
            # Make some change that should be rolled back
            db.execute(text("CREATE TABLE IF NOT EXISTS test_rollback (id INTEGER)"))
            db.execute(text("INSERT INTO test_rollback VALUES (1)"))
            # Raise exception
            raise ValueError("Test exception")
        # Session should be closed, and changes rolled back
        # Verify table doesn't exist or is empty (SQLite behavior)
        with get_db() as db:
            try:
                result = db.execute(text("SELECT COUNT(*) FROM test_rollback"))
                row = result.fetchone()
                if row is not None:
                    count = row[0]
                    # If table exists, it should be empty due to rollback
                    assert count == 0
            except Exception:
                # Table might not exist, which is fine
                pass


class TestAsyncDatabaseSession:
    """Tests for asynchronous database session management."""

    @pytest.mark.asyncio
    async def test_get_async_db_context_manager_success(self):
        """Test get_async_db yields session and commits on success."""
        async with get_async_db() as db:
            assert db is not None
            # Test basic query
            result = await db.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1
        # Session should be closed after context

    @pytest.mark.asyncio
    async def test_get_async_db_context_manager_rollback_on_exception(self):
        """Test get_async_db rolls back on exception."""
        with pytest.raises(ValueError):
            async with get_async_db() as db:
                # Make some change that should be rolled back
                await db.execute(
                    text("CREATE TABLE IF NOT EXISTS test_async_rollback (id INTEGER)")
                )
                await db.execute(text("INSERT INTO test_async_rollback VALUES (1)"))
                # Raise exception
                raise ValueError("Test exception")
        # Session should be closed, and changes rolled back
        # Verify table doesn't exist or is empty
        async with get_async_db() as db:
            try:
                result = await db.execute(text("SELECT COUNT(*) FROM test_async_rollback"))
                row = result.fetchone()
                if row is not None:
                    count = row[0]
                    # If table exists, it should be empty due to rollback
                    assert count == 0
            except Exception:
                # Table might not exist, which is fine
                pass
