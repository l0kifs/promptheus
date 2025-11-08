"""Health check API router for FastAPI."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from promptheus.core.dependency_container import DependencyContainer
from promptheus.health import HealthService

router = APIRouter()


def get_health_service() -> HealthService:
    """Get health service from container."""
    container = DependencyContainer.get_instance()
    # Get database session maker from container
    db_session_maker = container.get_component("async_session_maker")
    # Get AI client from container
    ai_client = container.get_component("ai_client")

    return HealthService(
        db_session_maker=db_session_maker,
        ai_client=ai_client,
    )


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint returning system status.

    Returns:
        JSONResponse with health status and component details.
    """
    try:
        health_service = get_health_service()
        result = await health_service.check_health()

        # Return appropriate HTTP status based on health
        status_code = 200 if result["status"] == "healthy" else 503

        return JSONResponse(
            content=result,
            status_code=status_code,
        )
    except Exception as e:
        # Return service unavailable if health check itself fails
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "version": "0.1.0",
            },
            status_code=503,
        )
