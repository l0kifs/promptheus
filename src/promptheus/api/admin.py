"""Admin API endpoints for cache management and system administration."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel

from promptheus.core.dependency_container import DependencyContainer


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    total_cached: int
    skill_levels: list[str]
    hits: int
    misses: int
    hit_rate: float
    sets: int
    deletes: int
    clears: int
    reloads: int


class CacheClearResponse(BaseModel):
    """Response model for cache clear operation."""

    lessons_cleared: int
    message: str


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    cache_stats: CacheStatsResponse | None = None
    message: str


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats() -> CacheStatsResponse:
    """Get cache statistics.

    Returns:
        Cache statistics including hits, misses, and hit rate
    """
    try:
        container = DependencyContainer.get_instance()
        cache = container.get_component("lesson_cache")
        stats = await cache.get_stats()

        return CacheStatsResponse(
            total_cached=stats["total_cached"],
            skill_levels=stats["skill_levels"],
            hits=stats["hits"],
            misses=stats["misses"],
            hit_rate=stats["hit_rate"],
            sets=stats["sets"],
            deletes=stats["deletes"],
            clears=stats["clears"],
            reloads=stats["reloads"],
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache not available",
        ) from e
    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics",
        ) from e


@router.post("/cache/clear", response_model=CacheClearResponse)
async def clear_cache() -> CacheClearResponse:
    """Clear all lessons from cache.

    Returns:
        Number of lessons cleared
    """
    try:
        container = DependencyContainer.get_instance()
        cache = container.get_component("lesson_cache")
        cleared_count = await cache.clear()

        logger.info("Cache cleared via API", lessons_cleared=cleared_count)

        return CacheClearResponse(
            lessons_cleared=cleared_count,
            message=f"Successfully cleared {cleared_count} lessons from cache",
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache not available",
        ) from e
    except Exception as e:
        logger.error("Error clearing cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache",
        ) from e


@router.post("/lessons/reload")
async def reload_lessons() -> dict[str, Any]:
    """Reload all lessons from filesystem.

    Returns:
        Reload results by skill level
    """
    try:
        container = DependencyContainer.get_instance()
        lesson_loader = await container.get_lesson_loader_service()

        # Reload all lessons
        loaded_count = await lesson_loader.batch_load_all()

        logger.info("Lessons reloaded via API", lessons_loaded=loaded_count)

        return {
            "message": f"Successfully reloaded {loaded_count} lessons",
            "lessons_loaded": loaded_count,
        }
    except Exception as e:
        logger.error("Error reloading lessons", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload lessons: {str(e)}",
        ) from e


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Comprehensive health check including cache status.

    Returns:
        Health status with cache statistics
    """
    try:
        container = DependencyContainer.get_instance()
        # Check cache status
        cache_stats = None
        try:
            cache = container.get_component("lesson_cache")
            stats = await cache.get_stats()
            cache_stats = CacheStatsResponse(
                total_cached=stats["total_cached"],
                skill_levels=stats["skill_levels"],
                hits=stats["hits"],
                misses=stats["misses"],
                hit_rate=stats["hit_rate"],
                sets=stats["sets"],
                deletes=stats["deletes"],
                clears=stats["clears"],
                reloads=stats["reloads"],
            )
        except KeyError:
            logger.debug("Cache not available for health check")
        except Exception as e:
            logger.warning("Error getting cache stats for health check", error=str(e))

        return HealthResponse(
            status="healthy",
            cache_stats=cache_stats,
            message="System is healthy",
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed",
        ) from e
