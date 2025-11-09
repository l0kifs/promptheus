"""Tests for bot middleware and error handling."""

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from promptheus.bot.base_handlers import BaseBotHandlers
from promptheus.bot.middleware.rate_limiter import RateLimitMiddleware
from promptheus.core.rate_limit_service import RateLimitService


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    @pytest.fixture
    def rate_limit_service(self):
        """Create rate limit service."""
        return RateLimitService(requests_per_minute=5)

    @pytest.fixture
    def middleware(self, rate_limit_service):
        """Create rate limit middleware."""
        return RateLimitMiddleware(rate_limit_service)

    @pytest.fixture
    def mock_update(self, mocker):
        """Create mock update with user."""
        update = mocker.Mock(spec=Update)
        user = mocker.Mock()
        user.id = 12345
        update.effective_user = user
        update.effective_message = mocker.AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self, mocker):
        """Create mock context."""
        return mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.fixture
    def mock_callback(self, mocker):
        """Create mock callback."""
        return mocker.AsyncMock(return_value="callback_result")

    @pytest.mark.asyncio
    async def test_middleware_allows_request_under_limit(
        self, middleware, mock_update, mock_context, mock_callback
    ):
        """Test middleware allows requests under rate limit."""
        result = await middleware(mock_update, mock_context, mock_callback)

        # Should call callback and return its result
        mock_callback.assert_called_once_with(mock_update, mock_context)
        assert result == "callback_result"

        # Should not send rate limit message
        mock_update.effective_message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_blocks_request_over_limit(
        self, middleware, mock_update, mock_context, mock_callback, rate_limit_service
    ):
        """Test middleware blocks requests over rate limit."""
        # Hit the rate limit first
        for _ in range(5):
            await rate_limit_service.check_limit(12345)

        result = await middleware(mock_update, mock_context, mock_callback)

        # Should not call callback
        mock_callback.assert_not_called()
        # Should return None (blocked)
        assert result is None

        # Should send rate limit message
        mock_update.effective_message.reply_text.assert_called_once()
        message = mock_update.effective_message.reply_text.call_args[0][0]
        assert "Too many requests" in message
        assert "min" in message

    @pytest.mark.asyncio
    async def test_middleware_skips_non_user_updates(self, middleware, mocker):
        """Test middleware skips updates without effective user."""
        update = mocker.Mock(spec=Update)
        update.effective_user = None
        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
        callback = mocker.AsyncMock(return_value="result")

        result = await middleware(update, context, callback)

        # Should call callback directly
        callback.assert_called_once_with(update, context)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_middleware_handles_reply_error(
        self, middleware, mock_update, mock_context, mock_callback, rate_limit_service, mocker
    ):
        """Test middleware handles errors when sending rate limit message."""
        # Hit the rate limit
        for _ in range(5):
            await rate_limit_service.check_limit(12345)

        # Make reply_text raise an exception
        mock_update.effective_message.reply_text.side_effect = Exception("Send failed")

        # Should not crash, just log the error
        result = await middleware(mock_update, mock_context, mock_callback)

        assert result is None
        mock_callback.assert_not_called()


class TestBaseBotHandlersErrorHandling:
    """Tests for enhanced error handling in BaseBotHandlers."""

    @pytest.fixture
    def mock_dependencies(self, mocker):
        """Create mock dependencies."""
        return {
            "ai_client": mocker.Mock(),
            "assessment_engine": mocker.Mock(),
            "learning_orchestrator": mocker.Mock(),
            "progress_tracker": mocker.Mock(),
            "rate_limit_service": mocker.Mock(),
        }

    @pytest.fixture
    def handlers(self, mock_dependencies):
        """Create BaseBotHandlers instance."""
        return BaseBotHandlers(**mock_dependencies)

    @pytest.fixture
    def mock_update(self, mocker):
        """Create mock update with user and message."""
        update = mocker.Mock(spec=Update)
        user = mocker.Mock()
        user.id = 12345
        update.effective_user = user
        update.effective_message = mocker.AsyncMock()
        return update

    def test_classify_error_network_error(self, handlers):
        """Test error classification for network errors."""
        import httpx

        error = httpx.TimeoutException("timeout")
        category = handlers._classify_error(error)
        assert category == "api_error"

    def test_classify_error_user_error(self, handlers):
        """Test error classification for user errors."""
        error = ValueError("invalid input")
        category = handlers._classify_error(error)
        assert category == "user_error"

    def test_classify_error_system_error(self, handlers):
        """Test error classification for system errors."""
        error = RuntimeError("system failure")
        category = handlers._classify_error(error)
        assert category == "system_error"

    @pytest.mark.asyncio
    async def test_handle_api_error(self, handlers, mock_update, mocker):
        """Test API error handling."""
        # Mock logger to verify logging
        mock_logger = mocker.patch("promptheus.bot.base_handlers.logger")

        error = Exception("API timeout")

        await handlers._handle_api_error(mock_update, error)

        # Verify logging
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[1]["user_id"] == 12345
        assert "API error occurred" in call_args[0][0]

        # Verify message sent
        mock_update.effective_message.reply_text.assert_called_once()
        message = mock_update.effective_message.reply_text.call_args[0][0]
        assert "request took too long" in message.lower()

    @pytest.mark.asyncio
    async def test_handle_user_error(self, handlers, mock_update, mocker):
        """Test user error handling."""
        mock_logger = mocker.patch("promptheus.bot.base_handlers.logger")

        error = ValueError("invalid data")

        await handlers._handle_user_error(mock_update, error)

        # Verify logging
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["user_id"] == 12345

        # Verify message sent
        mock_update.effective_message.reply_text.assert_called_once()
        message = mock_update.effective_message.reply_text.call_args[0][0]
        assert "Something went wrong" in message
        assert "returning to the main menu" in message

    @pytest.mark.asyncio
    async def test_handle_system_error(self, handlers, mock_update, mocker):
        """Test system error handling."""
        mock_logger = mocker.patch("promptheus.bot.base_handlers.logger")

        error = RuntimeError("system crash")

        await handlers._handle_system_error(mock_update, error)

        # Verify logging
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[1]["user_id"] == 12345

        # Verify message sent
        mock_update.effective_message.reply_text.assert_called_once()
        message = mock_update.effective_message.reply_text.call_args[0][0]
        assert "internal error" in message

    @pytest.mark.asyncio
    async def test_error_handler_api_error(self, handlers, mock_update, mocker):
        """Test full error handler with API error."""
        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
        import httpx

        context.error = httpx.TimeoutException("timeout")

        await handlers.error_handler(mock_update, context)

        # Should handle as API error
        mock_update.effective_message.reply_text.assert_called_once()
        message = mock_update.effective_message.reply_text.call_args[0][0]
        assert "request took too long" in message.lower()

    @pytest.mark.asyncio
    async def test_error_handler_user_error(self, handlers, mock_update, mocker):
        """Test full error handler with user error."""
        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.error = ValueError("invalid input")

        await handlers.error_handler(mock_update, context)

        # Should handle as user error
        mock_update.effective_message.reply_text.assert_called_once()
        message = mock_update.effective_message.reply_text.call_args[0][0]
        assert "Something went wrong" in message

    @pytest.mark.asyncio
    async def test_error_handler_system_error(self, handlers, mock_update, mocker):
        """Test full error handler with system error."""
        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.error = RuntimeError("system failure")

        await handlers.error_handler(mock_update, context)

        # Should handle as system error
        mock_update.effective_message.reply_text.assert_called_once()
        message = mock_update.effective_message.reply_text.call_args[0][0]
        assert "internal error" in message

    @pytest.mark.asyncio
    async def test_error_handler_no_error(self, handlers, mock_update, mocker):
        """Test error handler with no error in context."""
        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.error = None

        # Should not crash and not send messages
        await handlers.error_handler(mock_update, context)

        mock_update.effective_message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_handler_invalid_update(self, handlers, mocker):
        """Test error handler with invalid update."""
        # Update without effective_user
        update = mocker.Mock(spec=Update)
        update.effective_user = None

        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.error = RuntimeError("test error")

        # Should not crash
        await handlers.error_handler(update, context)

    @pytest.mark.asyncio
    async def test_error_handler_reply_failure(self, handlers, mock_update, mocker):
        """Test error handler when reply fails."""
        # Make reply_text fail
        mock_update.effective_message.reply_text.side_effect = Exception("Send failed")

        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.error = ValueError("test error")

        # Should not crash despite reply failure
        await handlers.error_handler(mock_update, context)

        # Reply was attempted
        mock_update.effective_message.reply_text.assert_called_once()
