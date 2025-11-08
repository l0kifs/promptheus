"""Tests for rate limiting service."""

import asyncio
import time

import pytest

from promptheus.core.rate_limit_service import RateLimitService


class TestRateLimitService:
    """Tests for RateLimitService."""

    @pytest.fixture
    def rate_limit_service(self):
        """Create rate limit service with default settings."""
        return RateLimitService(requests_per_minute=10)

    @pytest.fixture
    def fast_rate_limit_service(self):
        """Create rate limit service with fast settings for testing."""
        return RateLimitService(requests_per_minute=5)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test service initialization with custom settings."""
        service = RateLimitService(requests_per_minute=5)
        assert service.requests_per_minute == 5
        assert service.window_seconds == 60

    @pytest.mark.asyncio
    async def test_check_limit_allows_initial_requests(self, rate_limit_service):
        """Test that initial requests are allowed."""
        user_id = 12345

        # First 10 requests should be allowed
        for _ in range(10):
            allowed = await rate_limit_service.check_limit(user_id)
            assert allowed is True

    @pytest.mark.asyncio
    async def test_check_limit_blocks_excess_requests(self, rate_limit_service):
        """Test that 11th request is blocked."""
        user_id = 12345
        allowed = True

        # Send 11 requests
        for _ in range(11):
            allowed = await rate_limit_service.check_limit(user_id)

        # 11th should be blocked
        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_limit_resets_after_window(self, fast_rate_limit_service):
        """Test that rate limit resets after time window."""
        user_id = 12345
        service = fast_rate_limit_service  # 5 requests per minute

        # Send 5 requests to hit the limit
        for _ in range(5):
            allowed = await service.check_limit(user_id)
            assert allowed is True

        # 6th should be blocked
        allowed = await service.check_limit(user_id)
        assert allowed is False

        # Simulate time passing (61 seconds to ensure window reset)
        # We need to manipulate the internal timestamps
        original_time = time.time()
        time_module = time
        original_time_func = time_module.time

        try:
            # Mock time.time to return a time 61 seconds later
            def mock_time():
                return original_time + 61  # 61 seconds later

            time_module.time = mock_time

            # Now the request should be allowed again
            allowed = await service.check_limit(user_id)
            assert allowed is True

        finally:
            # Restore original time function
            time_module.time = original_time_func

    @pytest.mark.asyncio
    async def test_get_remaining_time_no_requests(self, rate_limit_service):
        """Test remaining time when no requests made."""
        user_id = 12345

        remaining = await rate_limit_service.get_remaining_time(user_id)
        assert remaining == 0.0

    @pytest.mark.asyncio
    async def test_get_remaining_time_with_requests(self, rate_limit_service):
        """Test remaining time calculation with active requests."""
        user_id = 12345

        # Make some requests
        for _ in range(3):
            await rate_limit_service.check_limit(user_id)

        remaining = await rate_limit_service.get_remaining_time(user_id)
        # Should be close to 60 seconds (full window)
        assert 50 <= remaining <= 60

    @pytest.mark.asyncio
    async def test_get_request_count(self, rate_limit_service):
        """Test getting current request count."""
        user_id = 12345

        # Initially 0
        count = await rate_limit_service.get_request_count(user_id)
        assert count == 0

        # After 3 requests
        for _ in range(3):
            await rate_limit_service.check_limit(user_id)

        count = await rate_limit_service.get_request_count(user_id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_reset_user(self, rate_limit_service):
        """Test resetting rate limit for a user."""
        user_id = 12345

        # Make some requests
        for _ in range(3):
            await rate_limit_service.check_limit(user_id)

        # Verify requests are tracked
        count = await rate_limit_service.get_request_count(user_id)
        assert count == 3

        # Reset user
        await rate_limit_service.reset_user(user_id)

        # Verify reset
        count = await rate_limit_service.get_request_count(user_id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_cleanup_inactive_users(self, rate_limit_service):
        """Test cleanup of inactive users."""
        # Add some mock timestamps that are old
        user_id = 12345
        current_time = time.time()

        # Manually add old timestamps (2 hours ago)
        rate_limit_service._request_history[user_id] = [current_time - 7200]

        # Cleanup should remove this user
        removed_count = await rate_limit_service.cleanup_inactive_users(max_age_seconds=3600)
        assert removed_count == 1

        # Verify user was removed
        count = await rate_limit_service.get_request_count(user_id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_multiple_users_isolated(self, rate_limit_service):
        """Test that different users have isolated rate limits."""
        user1_id = 12345
        user2_id = 67890

        # User 1 makes requests up to the limit
        for _ in range(10):
            allowed = await rate_limit_service.check_limit(user1_id)
            assert allowed is True

        # User 2 should still be allowed (separate limit)
        allowed = await rate_limit_service.check_limit(user2_id)
        assert allowed is True

        # User 1's 11th request should be blocked
        allowed = await rate_limit_service.check_limit(user1_id)
        assert allowed is False

        # But user 2 can still make requests
        for _ in range(5):
            allowed = await rate_limit_service.check_limit(user2_id)
            assert allowed is True

    @pytest.mark.asyncio
    async def test_concurrent_requests_thread_safety(self, rate_limit_service):
        """Test that concurrent requests are handled safely."""
        user_id = 12345

        async def make_request():
            return await rate_limit_service.check_limit(user_id)

        # Launch multiple concurrent requests
        tasks = [make_request() for _ in range(15)]
        results = await asyncio.gather(*tasks)

        # Should allow exactly 10 requests
        allowed_count = sum(1 for result in results if result)
        blocked_count = sum(1 for result in results if not result)

        assert allowed_count == 10
        assert blocked_count == 5
