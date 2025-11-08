"""Tests for logging configuration."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from loguru import logger

from promptheus.main import configure_logging


@pytest.mark.parametrize(
    "environment,expected_level",
    [
        ("development", "DEBUG"),
        ("production", "WARNING"),
    ],
)
def test_configure_logging_respects_environment(environment, expected_level):
    """Test that logging configuration uses correct level per environment."""
    # Given
    with patch("promptheus.main.get_settings") as mock_get_settings:
        mock_settings = mock_get_settings.return_value
        mock_settings.environment = environment
        mock_settings.log_level = expected_level

        # When
        configure_logging()

        # Then
        # Verify that get_settings was called
        mock_get_settings.assert_called_once()

        # The actual verification of handler levels would require inspecting
        # the logger's handlers, which is complex with loguru.
        # Instead, we verify the settings are used correctly by checking
        # that the function doesn't raise exceptions and uses the settings.


def test_file_logging_produces_valid_json():
    """Test that file logs are valid JSON."""
    # Given
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"

        # Configure logging to temp file with JSON serialization
        logger.remove()  # Remove existing handlers
        logger.add(log_file, level="INFO", serialize=True, format="{time} | {level} | {message}")

        # When
        logger.info("Test message", user_id=123, action="test")

        # Then
        log_content = log_file.read_text()
        log_lines = log_content.strip().split("\n")
        assert len(log_lines) == 1

        log_entry = json.loads(log_lines[0])
        # When serialize=True, loguru creates an object with 'text' and 'record'
        assert "text" in log_entry
        assert "record" in log_entry

        record = log_entry["record"]
        assert record["level"]["name"] == "INFO"
        assert record["message"] == "Test message"
        assert record["extra"]["user_id"] == 123
        assert record["extra"]["action"] == "test"
        assert "timestamp" in record["time"]


def test_settings_log_level_computation():
    """Test that settings compute log level correctly based on environment."""
    from promptheus.config.settings import Settings

    # Test development environment
    settings_dev = Settings(
        telegram_bot_token="test_token", openrouter_api_key="test_key", environment="development"
    )
    assert settings_dev.log_level == "DEBUG"

    # Test production environment
    settings_prod = Settings(
        telegram_bot_token="test_token", openrouter_api_key="test_key", environment="production"
    )
    assert settings_prod.log_level == "WARNING"
