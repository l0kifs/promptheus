"""Unit and integration tests for OpenRouterClient."""

from unittest.mock import Mock

import httpx
import pytest

from promptheus.ai.openrouter_client import OpenRouterClient


class TestOpenRouterClient:
    """Tests for OpenRouterClient."""

    @pytest.fixture
    def mock_settings(self, mocker):
        """Mock settings for testing."""
        mock_settings = Mock()
        mock_settings.openrouter_api_key = "test-api-key"
        mock_settings.ai_model_primary = "gpt-3.5-turbo"
        mock_settings.ai_model_fallback = "gpt-4"
        mock_settings.ai_model_alternative = "claude-3-haiku"
        mock_settings.max_tokens_feedback = 500
        mock_settings.temperature_feedback = 0.3
        mocker.patch("promptheus.ai.openrouter_client.get_settings", return_value=mock_settings)
        return mock_settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create OpenRouterClient instance."""
        return OpenRouterClient()

    def test_init_sets_correct_headers_and_url(self, client, mock_settings):
        """Test that client initializes with correct headers and URL."""
        assert client.base_url == "https://openrouter.ai/api/v1"
        assert client.headers["Authorization"] == f"Bearer {mock_settings.openrouter_api_key}"
        assert client.headers["HTTP-Referer"] == "https://github.com/l0kifs/promptheus"
        assert client.headers["X-Title"] == "Promptheus Bot"
        assert client.timeout == 10.0

    @pytest.mark.asyncio
    async def test_call_model_success(self, client, respx_mock):
        """Test successful model call."""
        # Mock successful API response
        mock_response = {"choices": [{"message": {"content": "Test response"}}]}

        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=200, json=mock_response
        )

        result = await client.call_model(
            prompt="Test prompt", model="gpt-3.5-turbo", max_tokens=100, temperature=0.7
        )

        assert result == "Test response"

    @pytest.mark.asyncio
    async def test_call_model_http_error(self, client, respx_mock):
        """Test HTTP error handling."""
        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=500, json={"error": "Internal server error"}
        )

        with pytest.raises(httpx.HTTPError):
            await client.call_model("Test prompt", "gpt-3.5-turbo")

    @pytest.mark.asyncio
    async def test_call_model_timeout(self, client, respx_mock):
        """Test timeout handling."""
        respx_mock.post(
            "https://openrouter.ai/api/v1/chat/completions"
        ).side_effect = httpx.TimeoutException("Timeout")

        with pytest.raises(httpx.HTTPError):
            await client.call_model("Test prompt", "gpt-3.5-turbo")

    @pytest.mark.asyncio
    async def test_call_model_invalid_response_format(self, client, respx_mock):
        """Test handling of invalid response format."""
        # Response missing choices
        mock_response = {"invalid": "format"}

        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=200, json=mock_response
        )

        with pytest.raises(KeyError):
            await client.call_model("Test prompt", "gpt-3.5-turbo")

    @pytest.mark.asyncio
    async def test_call_with_fallback_primary_success(self, client, respx_mock, mock_settings):
        """Test fallback chain when primary model succeeds."""
        mock_response = {"choices": [{"message": {"content": "Primary response"}}]}

        # Only primary model responds
        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=200, json=mock_response
        )

        result = await client.call_with_fallback("Test prompt")

        assert result == "Primary response"

    @pytest.mark.asyncio
    async def test_call_with_fallback_to_secondary(self, client, respx_mock, mock_settings):
        """Test fallback to secondary model when primary fails."""
        # Mock primary model failure, secondary success
        route = respx_mock.post("https://openrouter.ai/api/v1/chat/completions")

        # First call (primary) fails
        route.side_effect = [
            httpx.HTTPError("Primary failed"),
            # Second call (secondary) succeeds
            httpx.Response(200, json={"choices": [{"message": {"content": "Secondary response"}}]}),
        ]

        result = await client.call_with_fallback("Test prompt")

        assert result == "Secondary response"

    @pytest.mark.asyncio
    async def test_call_with_fallback_to_alternative(self, client, respx_mock, mock_settings):
        """Test fallback to alternative model when both primary and secondary fail."""
        route = respx_mock.post("https://openrouter.ai/api/v1/chat/completions")

        # First two calls fail, third succeeds
        route.side_effect = [
            httpx.HTTPError("Primary failed"),
            httpx.HTTPError("Secondary failed"),
            httpx.Response(
                200, json={"choices": [{"message": {"content": "Alternative response"}}]}
            ),
        ]

        result = await client.call_with_fallback("Test prompt")

        assert result == "Alternative response"

    @pytest.mark.asyncio
    async def test_call_with_fallback_unexpected_error(self, client, respx_mock, mock_settings):
        """Test fallback chain with unexpected error that doesn't trigger continue."""
        # This is a rare edge case where an exception occurs that doesn't match our expected patterns
        # We'll mock the call_model to raise an unexpected exception on the last model
        original_call_model = client.call_model
        call_count = 0

        async def mock_call_model(prompt, model, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First two models fail
                raise httpx.HTTPError("Model failed")
            else:  # Third model raises unexpected error
                raise ValueError("Unexpected error")

        client.call_model = mock_call_model

        try:
            with pytest.raises(RuntimeError, match="All AI models failed"):
                await client.call_with_fallback("Test prompt")
        finally:
            client.call_model = original_call_model

    @pytest.mark.asyncio
    async def test_evaluate_prompt_success(self, client, respx_mock, mock_settings):
        """Test successful prompt evaluation."""
        ai_response = """Score: 8/10
Missing: Add context, specify output format
Good: Clear objective, good structure
Improved: Create a prompt that defines the AI role and provides context."""

        mock_response = {"choices": [{"message": {"content": ai_response}}]}

        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=200, json=mock_response
        )

        result = await client.evaluate_prompt("Test user prompt", "Test scenario")

        assert result["score"] == 8
        assert "Add context" in result["missing"]
        assert "Clear objective" in result["good"]
        assert "Create a prompt" in result["improved"]

    @pytest.mark.asyncio
    async def test_evaluate_prompt_parse_score_with_text(self, client, respx_mock, mock_settings):
        """Test score parsing with different formats."""
        ai_response = """Score: 7
Missing: Nothing specific
Good: Good structure
Improved: Better prompt"""

        mock_response = {"choices": [{"message": {"content": ai_response}}]}

        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=200, json=mock_response
        )

        result = await client.evaluate_prompt("Test prompt", "Test scenario")

        assert result["score"] == 7

    @pytest.mark.asyncio
    async def test_evaluate_prompt_invalid_score(self, client, respx_mock, mock_settings):
        """Test handling of invalid score format."""
        ai_response = """Score: invalid
Missing: Test
Good: Test
Improved: Test"""

        mock_response = {"choices": [{"message": {"content": ai_response}}]}

        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=200, json=mock_response
        )

        result = await client.evaluate_prompt("Test prompt", "Test scenario")

        # Should default to 5 when parsing fails
        assert result["score"] == 5

    @pytest.mark.asyncio
    async def test_evaluate_prompt_ai_error_returns_default(
        self, client, respx_mock, mock_settings
    ):
        """Test error handling in evaluate_prompt."""
        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=500, json={"error": "AI service unavailable"}
        )

        result = await client.evaluate_prompt("Test prompt", "Test scenario")

        assert result["score"] == 0
        assert "Error evaluating prompt" in result["missing"]
        assert result["good"] == ""
        assert result["improved"] == ""

    @pytest.mark.asyncio
    async def test_evaluate_prompt_with_custom_settings(self, client, respx_mock, mock_settings):
        """Test that evaluate_prompt uses correct settings."""
        ai_response = """Score: 6
Missing: Test
Good: Test
Improved: Test"""

        mock_response = {"choices": [{"message": {"content": ai_response}}]}

        route = respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=200, json=mock_response
        )

        await client.evaluate_prompt("Test prompt", "Test scenario")

        # Verify the request was made with correct parameters
        assert len(route.calls) == 1
        request = route.calls[0].request
        import json

        request_data = json.loads(request.content.decode())

        assert request_data["max_tokens"] == mock_settings.max_tokens_feedback
        assert request_data["temperature"] == mock_settings.temperature_feedback
        assert (
            mock_settings.ai_model_primary in request_data["model"]
            or mock_settings.ai_model_fallback in request_data["model"]
            or mock_settings.ai_model_alternative in request_data["model"]
        )

    @pytest.mark.asyncio
    async def test_assess_skill_level_perfect_score(self, client):
        """Test skill level assessment with perfect score."""
        answers = [True, True, True, True, True]  # 5/5 correct
        result = await client.assess_skill_level(answers)

        assert result["score"] == 100
        assert result["level"] == "advanced"
        assert result["correct"] == 5
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_assess_skill_level_beginner_score(self, client):
        """Test skill level assessment for beginner."""
        answers = [True, False, False, False, False]  # 1/5 correct = 20%
        result = await client.assess_skill_level(answers)

        assert result["score"] == 20
        assert result["level"] == "beginner"
        assert result["correct"] == 1
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_assess_skill_level_intermediate_score(self, client):
        """Test skill level assessment for intermediate."""
        answers = [True, True, True, False, False]  # 3/5 correct = 60%
        result = await client.assess_skill_level(answers)

        assert result["score"] == 60
        assert result["level"] == "intermediate"
        assert result["correct"] == 3
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_assess_skill_level_empty_answers(self, client):
        """Test skill level assessment with empty answers."""
        answers = []
        result = await client.assess_skill_level(answers)

        assert result["score"] == 0
        assert result["level"] == "beginner"
        assert result["correct"] == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_real_api_call_flow(self, client, respx_mock):
        """Integration test simulating real API call flow."""
        # Simulate the full evaluation flow
        evaluation_response = """Score: 9/10
Missing: Consider edge cases
Good: Excellent structure and clarity
Improved: Your prompt is already very good. Consider adding specific examples for better results."""

        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").respond(
            status_code=200, json={"choices": [{"message": {"content": evaluation_response}}]}
        )

        user_prompt = "Write a summary of the given text."
        scenario = "Text summarization task"

        result = await client.evaluate_prompt(user_prompt, scenario)

        assert result["score"] == 9
        assert "edge cases" in result["missing"]
        assert "structure and clarity" in result["good"]
        assert "already very good" in result["improved"]

        # Verify request structure
        call = respx_mock.calls[0]
        import json

        request_data = json.loads(call.request.content.decode())

        assert "model" in request_data
        assert "messages" in request_data
        assert len(request_data["messages"]) == 1
        assert request_data["messages"][0]["role"] == "user"
        assert scenario in request_data["messages"][0]["content"]
        assert user_prompt in request_data["messages"][0]["content"]
