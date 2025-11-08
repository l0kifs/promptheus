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
        assert settings.log_level == "DEBUG"
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

    def test_settings_webhook_mode_requires_url(self, monkeypatch):
        """Test that webhook mode requires webhook_url."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
        monkeypatch.setenv("BOT_MODE", "webhook")
        # webhook_url not set

        with pytest.raises(ValueError, match="webhook_url is required when bot_mode is 'webhook'"):
            Settings()

    def test_settings_webhook_url_must_be_https(self, monkeypatch):
        """Test that webhook URL must use HTTPS protocol."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
        monkeypatch.setenv("BOT_MODE", "webhook")
        monkeypatch.setenv("WEBHOOK_URL", "http://example.com/webhook")  # HTTP not HTTPS

        with pytest.raises(ValueError, match="webhook_url must use HTTPS protocol"):
            Settings()

    def test_settings_webhook_port_must_be_valid(self, monkeypatch):
        """Test that webhook port must be one of allowed values."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
        monkeypatch.setenv("WEBHOOK_PORT", "9999")  # Invalid port

        with pytest.raises(ValueError, match="webhook_port must be one of"):
            Settings()

    def test_settings_valid_webhook_configuration(self, monkeypatch):
        """Test that valid webhook configuration is accepted."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
        monkeypatch.setenv("BOT_MODE", "webhook")
        monkeypatch.setenv("WEBHOOK_URL", "https://example.com/webhook")
        monkeypatch.setenv("WEBHOOK_SECRET", "secret123")
        monkeypatch.setenv("WEBHOOK_PORT", "8443")

        settings = Settings()

        assert settings.bot_mode == "webhook"
        assert settings.webhook_url == "https://example.com/webhook"
        assert settings.webhook_secret == "secret123"
        assert settings.webhook_port == 8443
        assert settings.webhook_path == "/webhook"  # default value

    def test_settings_polling_mode_default(self, monkeypatch):
        """Test that polling mode is default and doesn't require webhook config."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
        # BOT_MODE not set, should default to polling

        settings = Settings()

        assert settings.bot_mode == "polling"
        assert settings.webhook_url is None
        assert settings.webhook_secret is None
        assert settings.webhook_port == 8443  # default
        assert settings.webhook_path == "/webhook"  # default

    def test_settings_webhook_valid_ports(self, monkeypatch):
        """Test that all valid webhook ports are accepted."""
        valid_ports = [80, 88, 443, 8443]

        for port in valid_ports:
            monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
            monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
            monkeypatch.setenv("WEBHOOK_PORT", str(port))

            settings = Settings()
            assert settings.webhook_port == port


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
