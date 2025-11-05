"""Tests for dependency injection container."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.core.dependency_container import DependencyContainer
from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.core.progress_tracker import ProgressTracker
from promptheus.data.async_repositories import (
    AsyncLessonRepository,
    AsyncProgressRepository,
    AsyncSessionRepository,
    AsyncUserRepository,
)


class TestDependencyContainer:
    """Tests for DependencyContainer."""

    @pytest.fixture
    def container(self):
        """Get fresh container instance for each test."""
        # Reset singleton for testing
        DependencyContainer._instance = None
        container = DependencyContainer.get_instance()
        return container

    @pytest.fixture
    def mock_session_maker(self):
        """Mock async session maker."""
        return MagicMock()

    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client."""
        return MagicMock(spec=OpenRouterClient)

    @pytest.fixture
    def mock_assessment_engine(self):
        """Mock assessment engine."""
        return MagicMock(spec=AssessmentEngine)

    def test_singleton_pattern(self):
        """Test that DependencyContainer follows singleton pattern."""
        # Reset singleton
        DependencyContainer._instance = None

        container1 = DependencyContainer.get_instance()
        container2 = DependencyContainer.get_instance()

        assert container1 is container2
        assert isinstance(container1, DependencyContainer)

    def test_initialization_not_called_twice(self, container):
        """Test that initialize() is not called twice."""
        # Mock the initialization process
        container._async_engine = MagicMock()
        container._async_session_maker = MagicMock()
        container._components = {"ai_client": MagicMock()}

        # Set as initialized
        container._initialized = True

        # Should not raise error or re-initialize
        import asyncio

        asyncio.run(container.initialize())

        # Should still be initialized
        assert container._initialized is True

    def test_get_component_exists(self, container, mock_ai_client):
        """Test getting existing component."""
        container._register_component("ai_client", mock_ai_client)

        result = container.get_component("ai_client")
        assert result is mock_ai_client

    def test_get_component_not_found(self, container):
        """Test getting non-existent component raises ValueError."""
        with pytest.raises(ValueError, match="Component 'nonexistent' not found"):
            container.get_component("nonexistent")

    @pytest.mark.asyncio
    async def test_get_user_repository(self, container, mock_session_maker):
        """Test getting user repository with session."""
        container._async_session_maker = mock_session_maker
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        repo = await container.get_user_repository()

        assert isinstance(repo, AsyncUserRepository)
        assert repo.db is mock_session
        mock_session_maker.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_lesson_repository(self, container, mock_session_maker):
        """Test getting lesson repository with session."""
        container._async_session_maker = mock_session_maker
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        repo = await container.get_lesson_repository()

        assert isinstance(repo, AsyncLessonRepository)
        assert repo.db is mock_session

    @pytest.mark.asyncio
    async def test_get_progress_repository(self, container, mock_session_maker):
        """Test getting progress repository with session."""
        container._async_session_maker = mock_session_maker
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        repo = await container.get_progress_repository()

        assert isinstance(repo, AsyncProgressRepository)
        assert repo.db is mock_session

    @pytest.mark.asyncio
    async def test_get_session_repository(self, container, mock_session_maker):
        """Test getting session repository with session."""
        container._async_session_maker = mock_session_maker
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        repo = await container.get_session_repository()

        assert isinstance(repo, AsyncSessionRepository)
        assert repo.db is mock_session

    @pytest.mark.asyncio
    async def test_get_learning_flow_orchestrator(self, container, mock_session_maker):
        """Test getting learning flow orchestrator with dependencies."""
        container._async_session_maker = mock_session_maker
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        orchestrator = await container.get_learning_flow_orchestrator()

        assert isinstance(orchestrator, LearningFlowOrchestrator)
        assert isinstance(orchestrator.user_repo, AsyncUserRepository)
        assert isinstance(orchestrator.lesson_repo, AsyncLessonRepository)
        assert isinstance(orchestrator.session_repo, AsyncSessionRepository)

    @pytest.mark.asyncio
    async def test_get_progress_tracker(self, container, mock_session_maker):
        """Test getting progress tracker with repository."""
        container._async_session_maker = mock_session_maker
        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        tracker = await container.get_progress_tracker()

        assert isinstance(tracker, ProgressTracker)
        assert isinstance(tracker.progress_repo, AsyncProgressRepository)

    @pytest.mark.asyncio
    async def test_get_bot_handlers(
        self, container, mock_session_maker, mock_ai_client, mock_assessment_engine
    ):
        """Test getting bot handlers with all dependencies."""
        # Setup container
        container._async_session_maker = mock_session_maker
        container._register_component("ai_client", mock_ai_client)
        container._register_component("assessment_engine", mock_assessment_engine)

        mock_session = AsyncMock()
        mock_session_maker.return_value = mock_session

        # Mock the import to avoid circular imports in test
        with patch("promptheus.bot.handlers.BotHandlers") as mock_handlers_class:
            mock_handlers = MagicMock()
            mock_handlers_class.return_value = mock_handlers

            await container.get_bot_handlers()

            # Verify handlers were created with correct dependencies
            mock_handlers_class.assert_called_once()
            call_args = mock_handlers_class.call_args
            assert call_args[1]["ai_client"] is mock_ai_client
            assert call_args[1]["assessment_engine"] is mock_assessment_engine
            assert isinstance(call_args[1]["learning_orchestrator"], LearningFlowOrchestrator)
            assert isinstance(call_args[1]["progress_tracker"], ProgressTracker)

    @pytest.mark.asyncio
    async def test_cleanup(self, container):
        """Test cleanup method."""
        # Setup mock engine
        mock_engine = AsyncMock()
        container._async_engine = mock_engine
        container._components = {"comp1": MagicMock(), "comp2": MagicMock()}

        await container.cleanup()

        # Verify engine dispose was called
        mock_engine.dispose.assert_called_once()

        # Verify components cleared
        assert container._components == {}
        assert container._initialized is False
