"""Admin API endpoints for cache management and system administration."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel

from promptheus.core.dependency_container import DependencyContainer
from promptheus.data.schemas import (
    CreateVersionRequest,
    LessonVersionDetail,
    LessonVersionInfo,
    RollbackVersionRequest,
    VersionComparison,
)


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


@router.get("/lessons/{lesson_id}/versions", response_model=list[LessonVersionInfo])
async def get_lesson_versions(lesson_id: int) -> list[LessonVersionInfo]:
    """Get all versions for a specific lesson.

    Returns:
        List of lesson versions in chronological order
    """
    try:
        container = DependencyContainer.get_instance()
        version_repo = await container.get_version_repository()

        versions = await version_repo.find_all_by_lesson(lesson_id)
        return [
            LessonVersionInfo(
                id=v.id,
                version=v.version,
                content_hash=v.content_hash,
                is_active=v.is_active,
                created_at=v.created_at,
                created_by=v.created_by,
            )
            for v in versions
        ]
    except Exception as e:
        logger.error("Error getting lesson versions", lesson_id=lesson_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lesson versions",
        ) from e


@router.get("/lessons/{lesson_id}/versions/{version}", response_model=LessonVersionDetail)
async def get_lesson_version(lesson_id: int, version: str) -> LessonVersionDetail:
    """Get a specific version of a lesson.

    Returns:
        Detailed lesson version information
    """
    try:
        container = DependencyContainer.get_instance()
        version_repo = await container.get_version_repository()

        version_obj = await version_repo.find_by_lesson_and_version(lesson_id, version)
        if not version_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found for lesson {lesson_id}",
            )

        return LessonVersionDetail(
            id=version_obj.id,
            version=version_obj.version,
            content_hash=version_obj.content_hash,
            is_active=version_obj.is_active,
            created_at=version_obj.created_at,
            created_by=version_obj.created_by,
            content_snapshot=version_obj.content_snapshot,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting lesson version", lesson_id=lesson_id, version=version, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lesson version",
        ) from e


@router.post("/lessons/{lesson_id}/versions", response_model=LessonVersionInfo)
async def create_lesson_version(lesson_id: int, request: CreateVersionRequest) -> LessonVersionInfo:
    """Create a new version for a lesson.

    Returns:
        Created version information
    """
    try:
        container = DependencyContainer.get_instance()
        version_repo = await container.get_version_repository()
        version_manager = container.get_component("version_manager")

        # Get current active version
        current_active = await version_repo.find_active_by_lesson(lesson_id)
        if not current_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active version found for lesson {lesson_id}",
            )

        # Increment version
        new_version = version_manager.increment_version(current_active.version, request.bump_type)

        # Create new version
        version_obj = await version_repo.create(
            lesson_id=lesson_id,
            version=new_version,
            content_hash=current_active.content_hash,  # Same content, new version
            content_snapshot=current_active.content_snapshot,
            is_active=True,
            created_by="admin_api",
        )

        # Deactivate other versions
        await version_repo.deactivate_other_versions(lesson_id, version_obj.id)

        logger.info("Version created via API", lesson_id=lesson_id, version=new_version)

        return LessonVersionInfo(
            id=version_obj.id,
            version=version_obj.version,
            content_hash=version_obj.content_hash,
            is_active=version_obj.is_active,
            created_at=version_obj.created_at,
            created_by=version_obj.created_by,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating lesson version", lesson_id=lesson_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lesson version",
        ) from e


@router.post("/lessons/{lesson_id}/versions/rollback", response_model=LessonVersionInfo)
async def rollback_lesson_version(
    lesson_id: int, request: RollbackVersionRequest
) -> LessonVersionInfo:
    """Rollback a lesson to a previous version.

    Returns:
        The version that is now active
    """
    try:
        container = DependencyContainer.get_instance()
        version_repo = await container.get_version_repository()

        # Find target version
        target_version = await version_repo.find_by_lesson_and_version(
            lesson_id, request.target_version
        )
        if not target_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {request.target_version} not found for lesson {lesson_id}",
            )

        # Deactivate all other versions and activate target
        await version_repo.deactivate_other_versions(lesson_id, target_version.id)
        await version_repo.update_active_status(target_version.id, True)

        logger.info(
            "Version rollback completed",
            lesson_id=lesson_id,
            rolled_back_to=request.target_version,
        )

        return LessonVersionInfo(
            id=target_version.id,
            version=target_version.version,
            content_hash=target_version.content_hash,
            is_active=target_version.is_active,
            created_at=target_version.created_at,
            created_by=target_version.created_by,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error rolling back lesson version",
            lesson_id=lesson_id,
            target_version=request.target_version,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rollback lesson version",
        ) from e


@router.post("/lessons/{lesson_id}/versions/compare")
async def compare_lesson_versions(
    lesson_id: int, version1: str, version2: str
) -> VersionComparison:
    """Compare two versions of a lesson.

    Returns:
        Comparison result showing differences
    """
    try:
        container = DependencyContainer.get_instance()
        version_repo = await container.get_version_repository()
        version_manager = container.get_component("version_manager")

        # Get both versions
        v1 = await version_repo.find_by_lesson_and_version(lesson_id, version1)
        v2 = await version_repo.find_by_lesson_and_version(lesson_id, version2)

        if not v1 or not v2:
            missing = []
            if not v1:
                missing.append(version1)
            if not v2:
                missing.append(version2)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version(s) not found: {', '.join(missing)}",
            )

        # Compare versions
        comparison = version_manager.compare_versions(v1, v2)

        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error comparing lesson versions",
            lesson_id=lesson_id,
            version1=version1,
            version2=version2,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare lesson versions",
        ) from e
