"""Dependency injection container for managing application components."""

from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.ai.prompt_template_manager import PromptTemplateManager
from promptheus.config import get_settings
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.core.progress_tracker import ProgressTracker
from promptheus.core.rate_limit_service import RateLimitService
from promptheus.data.async_repositories import (
    AsyncLessonRepository,
    AsyncProgressRepository,
    AsyncSessionRepository,
    AsyncUserRepository,
)


class DependencyContainer:
    """Singleton dependency injection container."""

    _instance: "DependencyContainer | None" = None
    _initialized = False

    def __init__(self) -> None:
        """Initialize container - should not be called directly."""
        if DependencyContainer._instance is not None:
            raise RuntimeError("Use get_instance() to get DependencyContainer")
        self._components: dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> "DependencyContainer":
        """Get singleton instance of dependency container."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize all components asynchronously."""
        if self._initialized:
            logger.warning("Dependency container already initialized")
            return

        logger.info("Initializing dependency container")

        try:
            # Initialize database connection
            settings = get_settings()

            # Create async engine for repositories
            self._async_engine = create_async_engine(
                settings.database_url.replace("sqlite://", "sqlite+aiosqlite://")
                if "sqlite" in settings.database_url
                else settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
                echo=settings.environment == "development",
            )
            self._async_session_maker = async_sessionmaker(
                self._async_engine, expire_on_commit=False
            )

            # Initialize AI client
            ai_client = OpenRouterClient()
            self._register_component("ai_client", ai_client)

            # Initialize prompt template manager
            template_manager = PromptTemplateManager()
            self._register_component("template_manager", template_manager)

            # Initialize repositories (will be created per request with session)
            self._register_component("async_session_maker", self._async_session_maker)

            # Initialize core components
            assessment_engine = AssessmentEngine(ai_client, template_manager)
            self._register_component("assessment_engine", assessment_engine)

            # Initialize rate limit service
            rate_limit_service = RateLimitService()
            self._register_component("rate_limit_service", rate_limit_service)

            logger.info("Dependency container initialized successfully")
            self._initialized = True

        except Exception as e:
            logger.critical("Failed to initialize dependency container", error=str(e))
            raise

    def _register_component(self, name: str, component: Any) -> None:
        """Register a component in the container."""
        logger.debug("Registering component", name=name, component_type=type(component).__name__)
        self._components[name] = component

    def get_component(self, name: str) -> Any:
        """Get a component from the container."""
        if name not in self._components:
            raise ValueError(f"Component '{name}' not found in container")
        return self._components[name]

    # Factory methods for components that need database sessions
    async def get_user_repository(self) -> AsyncUserRepository:
        """Get UserRepository with async session maker."""
        return AsyncUserRepository(self._async_session_maker)

    async def get_lesson_repository(self) -> AsyncLessonRepository:
        """Get LessonRepository with async session maker."""
        return AsyncLessonRepository(self._async_session_maker)

    async def get_progress_repository(self) -> AsyncProgressRepository:
        """Get ProgressRepository with async session maker."""
        return AsyncProgressRepository(self._async_session_maker)

    async def get_session_repository(self) -> AsyncSessionRepository:
        """Get SessionRepository with async session maker."""
        return AsyncSessionRepository(self._async_session_maker)

    async def get_learning_flow_orchestrator(self) -> LearningFlowOrchestrator:
        """Get LearningFlowOrchestrator with repositories."""
        user_repo = await self.get_user_repository()
        lesson_repo = await self.get_lesson_repository()
        session_repo = await self.get_session_repository()
        return LearningFlowOrchestrator(user_repo, lesson_repo, session_repo)

    async def get_progress_tracker(self) -> ProgressTracker:
        """Get ProgressTracker with repository."""
        progress_repo = await self.get_progress_repository()
        return ProgressTracker(progress_repo)

    def get_rate_limit_service(self) -> RateLimitService:
        """Get RateLimitService."""
        return self.get_component("rate_limit_service")

    async def get_bot_handlers(self) -> "BotHandlers":  # type: ignore
        """Get BotHandlers with all dependencies."""
        # Import here to avoid circular imports
        from promptheus.bot.handlers import BotHandlers

        ai_client = self.get_component("ai_client")
        assessment_engine = self.get_component("assessment_engine")
        learning_orchestrator = await self.get_learning_flow_orchestrator()
        progress_tracker = await self.get_progress_tracker()
        rate_limit_service = self.get_rate_limit_service()

        return BotHandlers(
            ai_client=ai_client,
            assessment_engine=assessment_engine,
            learning_orchestrator=learning_orchestrator,
            progress_tracker=progress_tracker,
            rate_limit_service=rate_limit_service,
        )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up dependency container")
        if hasattr(self, "_async_engine"):
            await self._async_engine.dispose()
        self._components.clear()
        self._initialized = False
        logger.info("Dependency container cleaned up")
