"""Tests for health check functionality."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from promptheus.health import HealthService


class TestHealthService:
    """Test cases for HealthService."""

    @pytest.fixture
    def mock_session_maker(self):
        """Mock async session maker."""
        from unittest.mock import AsyncMock

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncContextManager:
            def __init__(self, session):
                self.session = session

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        # Create the session maker function that returns the context manager
        session_maker = AsyncMock(return_value=MockAsyncContextManager(mock_session))

        return session_maker

    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client."""
        client = MagicMock()
        client.test_connection = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    def health_service(self, mock_session_maker, mock_ai_client):
        """Create health service with mocked dependencies."""
        return HealthService(
            db_session_maker=mock_session_maker,
            ai_client=mock_ai_client,
            telegram_token="test_token",
        )

    @pytest.mark.asyncio
    async def test_check_health_all_healthy(self, health_service, mock_ai_client, monkeypatch):
        """Test health check when all services are healthy."""

        # Mock database check to return healthy
        async def mock_db_check():
            return {"status": "connected"}

        # Mock telegram check to return healthy
        async def mock_telegram_check():
            return {"status": "reachable"}

        # Mock AI connection
        mock_ai_client.test_connection = AsyncMock(return_value=True)

        monkeypatch.setattr(health_service, "_check_database", mock_db_check)
        monkeypatch.setattr(health_service, "_check_telegram_api", mock_telegram_check)

        result = await health_service.check_health()

        assert result["status"] == "healthy"
        assert result["database"]["status"] == "connected"
        assert result["telegram_api"]["status"] == "reachable"
        assert result["openrouter_api"]["status"] == "reachable"
        assert "version" in result

    @pytest.mark.asyncio
    async def test_check_health_database_failure(self, health_service):
        """Test health check when database connection fails."""
        # Create a health service with a failing session maker
        failing_maker = AsyncMock(side_effect=Exception("Connection failed"))
        failing_health_service = HealthService(
            db_session_maker=failing_maker, ai_client=MagicMock()
        )

        result = await failing_health_service.check_health()

        assert result["status"] == "unhealthy"
        assert result["database"]["status"] == "disconnected"
        assert "error" in result["database"]

    @pytest.mark.asyncio
    async def test_check_health_telegram_api_failure(self, health_service, monkeypatch):
        """Test health check when Telegram API is unreachable."""
        # Mock httpx to simulate timeout
        import httpx

        async def mock_get(*args, **kwargs):
            raise httpx.TimeoutException("Timeout")

        monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

        result = await health_service.check_health()

        assert result["status"] == "unhealthy"
        assert result["telegram_api"]["status"] == "unreachable"
        assert result["telegram_api"]["error"] == "Timeout"

    @pytest.mark.asyncio
    async def test_check_health_openrouter_api_failure(self, health_service, mock_ai_client):
        """Test health check when OpenRouter API connection fails."""
        # Mock failed AI connection
        mock_ai_client.test_connection = AsyncMock(side_effect=Exception("API Error"))

        result = await health_service.check_health()

        assert result["status"] == "unhealthy"
        assert result["openrouter_api"]["status"] == "unreachable"
        assert "error" in result["openrouter_api"]

    @pytest.mark.asyncio
    async def test_check_health_no_database_session_maker(self):
        """Test health check when no database session maker is provided."""
        health_service = HealthService(db_session_maker=None)

        result = await health_service.check_health()

        assert result["database"]["status"] == "unknown"
        assert "message" in result["database"]

    @pytest.mark.asyncio
    async def test_check_health_no_ai_client(self):
        """Test health check when no AI client is provided."""
        health_service = HealthService(ai_client=None)

        result = await health_service.check_health()

        # Should still work but use fallback HTTP request
        assert "openrouter_api" in result
