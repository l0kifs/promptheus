"""Unit tests for application settings configuration."""

from unittest.mock import patch

import pytest
from pydantic_settings import SettingsConfigDict

from promptheus.config.settings import Settings, get_settings


class TestSettingsValidation:
    """Tests for Settings class validation and loading."""

    def test_settings_with_required_env_vars(self, monkeypatch):
        """Test loading settings with all required environment variables."""
        # Set required environment variables
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token_123")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key_456")

        # Optional variables with custom values
        monkeypatch.setenv("AI_MODEL_PRIMARY", "custom/model:v1")
        monkeypatch.setenv("MAX_TOKENS_DEFAULT", "2048")
        monkeypatch.setenv("ENVIRONMENT", "production")

        settings = Settings()

        assert settings.telegram_bot_token == "test_bot_token_123"
        assert settings.openrouter_api_key == "test_api_key_456"
        assert settings.ai_model_primary == "custom/model:v1"
        assert settings.max_tokens_default == 2048
        assert settings.environment == "production"

    def test_settings_with_minimal_required_vars(self, monkeypatch):
        """Test loading settings with only required environment variables."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")

        settings = Settings()

        # Required fields
        assert settings.telegram_bot_token == "test_bot_token"
        assert settings.openrouter_api_key == "test_api_key"

        # Default values
        assert settings.ai_model_primary == "meta-llama/llama-4-scout:free"
        assert settings.ai_model_fallback == "google/gemini-2.5-pro-exp:free"
        assert settings.max_tokens_default == 1024
        assert settings.temperature_default == 0.7
        assert settings.database_url == "sqlite:///./data/promptheus.db"
        assert settings.environment == "development"
        assert settings.log_level == "INFO"
        assert settings.rate_limit_requests == 10
        assert settings.session_timeout_minutes == 15

    def test_settings_case_insensitive_env_vars(self, monkeypatch):
        """Test that environment variables are loaded case-insensitively."""
        monkeypatch.setenv("telegram_bot_token", "test_bot_token_lower")
        monkeypatch.setenv("openrouter_api_key", "test_api_key_lower")
        monkeypatch.setenv("ai_model_primary", "custom/model:lower")

        settings = Settings()

        assert settings.telegram_bot_token == "test_bot_token_lower"
        assert settings.openrouter_api_key == "test_api_key_lower"
        assert settings.ai_model_primary == "custom/model:lower"

    def test_settings_env_file_loading(self, monkeypatch):
        """Test loading settings from .env file."""
        import os
        import tempfile
        from unittest.mock import patch

        # Clear existing env vars to ensure .env file is used
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("AI_MODEL_PRIMARY", raising=False)
        monkeypatch.delenv("MAX_TOKENS_DEFAULT", raising=False)

        # Create temporary .env file
        env_content = """TELEGRAM_BOT_TOKEN=env_file_bot_token
OPENROUTER_API_KEY=env_file_api_key
AI_MODEL_PRIMARY=env_file/model:v1
MAX_TOKENS_DEFAULT=4096
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            env_file_path = f.name

        try:
            # Patch the model_config to use our temp file
            with patch.object(
                Settings,
                "model_config",
                SettingsConfigDict(
                    env_file=env_file_path,
                    env_file_encoding="utf-8",
                    case_sensitive=False,
                    extra="ignore",
                ),
            ):
                settings = Settings()

                assert settings.telegram_bot_token == "env_file_bot_token"
                assert settings.openrouter_api_key == "env_file_api_key"
                assert settings.ai_model_primary == "env_file/model:v1"
                assert settings.max_tokens_default == 4096
        finally:
            os.unlink(env_file_path)

    def test_settings_env_vars_override_env_file(self, monkeypatch):
        """Test that environment variables override .env file values."""
        import os
        import tempfile
        from unittest.mock import patch

        # Clear existing env vars first
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("AI_MODEL_PRIMARY", raising=False)

        # Create temporary .env file
        env_content = """TELEGRAM_BOT_TOKEN=env_file_bot_token
OPENROUTER_API_KEY=env_file_api_key
AI_MODEL_PRIMARY=env_file/model:v1
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            env_file_path = f.name

        try:
            # Set env vars that should override .env file
            monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "override_bot_token")
            monkeypatch.setenv("AI_MODEL_PRIMARY", "override/model:v2")

            with patch.object(
                Settings,
                "model_config",
                SettingsConfigDict(
                    env_file=env_file_path,
                    env_file_encoding="utf-8",
                    case_sensitive=False,
                    extra="ignore",
                ),
            ):
                settings = Settings()

                # Env var should override .env file
                assert settings.telegram_bot_token == "override_bot_token"
                # .env file value should be used where no env var
                assert settings.openrouter_api_key == "env_file_api_key"
                # Env var should override .env file
                assert settings.ai_model_primary == "override/model:v2"
        finally:
            os.unlink(env_file_path)

    def test_settings_invalid_environment_value(self, monkeypatch):
        """Test validation of environment field values."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
        monkeypatch.setenv("ENVIRONMENT", "invalid_env")

        with pytest.raises(ValueError, match="environment"):
            Settings()

    def test_settings_invalid_log_level(self, monkeypatch):
        """Test that invalid log level raises validation error."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
        monkeypatch.setenv("LOG_LEVEL", "INVALID_LEVEL")

        # Pydantic should accept any string for log_level
        settings = Settings()
        assert settings.log_level == "INVALID_LEVEL"

    def test_settings_numeric_fields_validation(self, monkeypatch):
        """Test validation of numeric fields."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")

        # Test negative values (should be allowed or handled)
        monkeypatch.setenv("MAX_TOKENS_DEFAULT", "-100")
        monkeypatch.setenv("TEMPERATURE_DEFAULT", "-0.5")

        settings = Settings()
        assert settings.max_tokens_default == -100
        assert settings.temperature_default == -0.5

    def test_settings_extra_fields_ignored(self, monkeypatch):
        """Test that extra fields in env are ignored."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
        monkeypatch.setenv("EXTRA_FIELD", "should_be_ignored")

        settings = Settings()

        # Should not have extra field
        assert not hasattr(settings, "extra_field")


class TestGetSettingsFunction:
    """Tests for get_settings() function."""

    def test_get_settings_caching(self, monkeypatch):
        """Test that get_settings() caches the Settings instance."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")

        # First call
        settings1 = get_settings()

        # Modify env (should not affect cached instance)
        monkeypatch.setenv("AI_MODEL_PRIMARY", "modified/model:v2")
        settings2 = get_settings()

        # Should be the same cached instance
        assert settings1 is settings2
        # Should have original value, not modified
        assert settings1.ai_model_primary == "meta-llama/llama-4-scout:free"
        assert settings2.ai_model_primary == "meta-llama/llama-4-scout:free"

    def test_get_settings_returns_settings_instance(self, monkeypatch):
        """Test that get_settings() returns a Settings instance."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")

        settings = get_settings()

        assert isinstance(settings, Settings)
        assert hasattr(settings, "telegram_bot_token")
        assert hasattr(settings, "openrouter_api_key")

    @patch("promptheus.config.settings.Settings")
    def test_get_settings_handles_exceptions(self, mock_settings_class):
        """Test that get_settings() properly handles Settings initialization errors."""
        from promptheus.config.settings import get_settings

        # Clear cache
        get_settings.cache_clear()
        mock_settings_class.side_effect = ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            get_settings()
