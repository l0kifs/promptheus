"""Health check service for monitoring application components."""

from typing import Any

import httpx
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.config import get_settings


class HealthService:
    """Service for performing health checks on application components."""

    def __init__(
        self,
        db_session_maker: async_sessionmaker[AsyncSession] | None = None,
        ai_client: OpenRouterClient | None = None,
        telegram_token: str | None = None,
    ) -> None:
        """Initialize health service with optional dependencies for testing."""
        self.settings = get_settings()
        self.db_session_maker = db_session_maker
        self.ai_client = ai_client
        self.telegram_token = telegram_token or self.settings.telegram_bot_token

    async def check_health(self) -> dict[str, Any]:
        """Perform comprehensive health check of all components.

        Returns:
            Dict containing health status and component details.
        """
        logger.debug("Performing comprehensive health check")

        results = {
            "status": "healthy",
            "version": "0.1.0",
            "database": await self._check_database(),
            "telegram_api": await self._check_telegram_api(),
            "openrouter_api": await self._check_openrouter_api(),
        }

        # Determine overall status - any component that's not healthy makes the whole system unhealthy
        healthy_statuses = {"connected", "reachable", "unknown"}
        unhealthy_components = []

        for component, status in results.items():
            if isinstance(status, dict):
                component_status = status.get("status")
                if component_status not in healthy_statuses:
                    unhealthy_components.append(component)

        if unhealthy_components:
            results["status"] = "unhealthy"
            logger.warning("Health check failed", unhealthy_components=unhealthy_components)
        else:
            logger.debug("Health check passed")

        return results

    async def _check_database(self) -> dict[str, str]:
        """Check database connectivity."""
        if not self.db_session_maker:
            return {"status": "unknown", "message": "Database session maker not available"}

        try:
            async with self.db_session_maker() as session:
                # Simple query to test connectivity
                await session.execute(text("SELECT 1"))
                return {"status": "connected"}
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {"status": "disconnected", "error": str(e)}

    async def _check_telegram_api(self) -> dict[str, str]:
        """Check Telegram API reachability."""
        try:
            # Use a simple HTTP request to Telegram API
            async with httpx.AsyncClient(
                timeout=self.settings.health_check_timeout_seconds
            ) as client:
                # Use getMe endpoint which doesn't require authentication details
                response = await client.get(
                    "https://api.telegram.org/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/getMe"
                )
                # We expect a 401 Unauthorized response for invalid token, which means API is reachable
                if response.status_code in [400, 401, 403]:
                    return {"status": "reachable"}
                else:
                    return {
                        "status": "unreachable",
                        "error": f"Unexpected status: {response.status_code}",
                    }
        except httpx.TimeoutException:
            return {"status": "unreachable", "error": "Timeout"}
        except Exception as e:
            logger.error("Telegram API health check failed", error=str(e))
            return {"status": "unreachable", "error": str(e)}

    async def _check_openrouter_api(self) -> dict[str, str]:
        """Check OpenRouter API reachability."""
        try:
            # Use the AI client if available, otherwise make direct HTTP request
            if self.ai_client:
                # Test with a minimal request that should not consume API limits
                await self.ai_client.test_connection()
                return {"status": "reachable"}
            else:
                # Fallback: direct HTTP request to OpenRouter API
                async with httpx.AsyncClient(
                    timeout=self.settings.health_check_timeout_seconds
                ) as client:
                    response = await client.get("https://openrouter.ai/api/v1/models")
                    if response.status_code == 200:
                        return {"status": "reachable"}
                    else:
                        return {"status": "unreachable", "error": f"Status: {response.status_code}"}
        except Exception as e:
            logger.error("OpenRouter API health check failed", error=str(e))
            return {"status": "unreachable", "error": str(e)}
