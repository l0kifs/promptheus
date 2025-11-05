"""E2E test configuration and fixtures."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from telegram import Update
from telegram.ext import Application, ContextTypes

from promptheus.core.dependency_container import DependencyContainer


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_telegram_app(mocker):
    """Create a mock Telegram Application for E2E testing."""
    # Mock the Application
    app = mocker.Mock(spec=Application)

    # Mock updater and its methods
    mock_updater = mocker.Mock()
    mock_updater.start_polling = AsyncMock()
    mock_updater.stop = AsyncMock()
    app.updater = mock_updater

    # Mock application lifecycle methods
    app.initialize = AsyncMock()
    app.start = AsyncMock()
    app.stop = AsyncMock()
    app.shutdown = AsyncMock()

    # Mock add_handler method to capture registered handlers
    app.add_handler = Mock()
    app.add_error_handler = Mock()

    return app


@pytest.fixture
async def dependency_container(mocker):
    """Create dependency container with mocked components for E2E testing."""
    # Mock all external dependencies
    mock_ai_client = mocker.Mock()
    mock_assessment_engine = mocker.Mock()
    mock_learning_orchestrator = mocker.Mock()
    mock_progress_tracker = mocker.Mock()

    # Mock database components
    mock_session_maker = mocker.Mock()
    mock_async_session = mocker.AsyncMock()
    mock_session_maker.return_value = mock_async_session

    container = DependencyContainer.get_instance()

    # Register mocked components
    container._register_component("ai_client", mock_ai_client)
    container._register_component("assessment_engine", mock_assessment_engine)
    container._register_component("async_session_maker", mock_session_maker)

    # Mock the factory methods
    container.get_user_repository = AsyncMock(return_value=mocker.AsyncMock())
    container.get_lesson_repository = AsyncMock(return_value=mocker.AsyncMock())
    container.get_progress_repository = AsyncMock(return_value=mocker.AsyncMock())
    container.get_session_repository = AsyncMock(return_value=mocker.AsyncMock())
    container.get_learning_flow_orchestrator = AsyncMock(return_value=mock_learning_orchestrator)
    container.get_progress_tracker = AsyncMock(return_value=mock_progress_tracker)

    # Create real BotHandlers with mocked dependencies
    from promptheus.bot.handlers import BotHandlers

    mock_bot_handlers = BotHandlers(
        ai_client=mock_ai_client,
        assessment_engine=mock_assessment_engine,
        learning_orchestrator=mock_learning_orchestrator,
        progress_tracker=mock_progress_tracker,
    )
    container.get_bot_handlers = AsyncMock(return_value=mock_bot_handlers)

    yield container

    # Cleanup
    await container.cleanup()


@pytest.fixture
def mock_update_factory(mocker):
    """Factory for creating mock Update objects."""

    def create_update(update_type="message", user_id=12345, username="testuser", **kwargs):
        """Create a mock Update object."""
        update = mocker.Mock(spec=Update)
        update.effective_user = mocker.Mock()
        update.effective_user.id = user_id
        update.effective_user.username = username

        if update_type == "message":
            update.message = mocker.Mock()
            update.message.text = kwargs.get("text", "/start")
            update.message.message_id = kwargs.get("message_id", 1)
            update.message.reply_text = AsyncMock()
            update.callback_query = None
        elif update_type == "callback" or update_type == "callback_query":
            update.callback_query = mocker.Mock()
            update.callback_query.data = kwargs.get(
                "callback_data", kwargs.get("data", "test_data")
            )
            update.callback_query.message = mocker.Mock()
            update.callback_query.message.message_id = kwargs.get("message_id", 1)
            update.callback_query.answer = AsyncMock()
            update.callback_query.edit_message_text = AsyncMock()
            update.message = None

        return update

    return create_update


@pytest.fixture
def mock_context_factory(mocker):
    """Factory for creating mock Context objects."""

    def create_context(**kwargs):
        """Create a mock ContextTypes object."""
        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = mocker.Mock()
        context.bot.send_message = AsyncMock()
        context.bot.edit_message_text = AsyncMock()
        context.bot.edit_message_reply_markup = AsyncMock()
        return context

    return create_context


@pytest.fixture
async def e2e_test_setup(
    mock_telegram_app, dependency_container, mock_update_factory, mock_context_factory
):
    """Complete E2E test setup with all mocked components."""
    return {
        "app": mock_telegram_app,
        "container": dependency_container,
        "update_factory": mock_update_factory,
        "context_factory": mock_context_factory,
    }
