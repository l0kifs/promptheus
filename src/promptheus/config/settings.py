"""Application settings using Pydantic."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Bot
    telegram_bot_token: str = Field(..., description="Telegram bot token")

    # OpenRouter AI
    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    ai_model_primary: str = Field(
        default="meta-llama/llama-4-scout:free",
        description="Primary AI model (109B MoE, 512K context)",
    )
    ai_model_fallback: str = Field(
        default="google/gemini-2.5-pro-exp:free",
        description="Fallback AI model (1M context, advanced reasoning)",
    )
    ai_model_alternative: str = Field(
        default="mistralai/mistral-small-3.1-24b-instruct:free",
        description="Alternative AI model (96K context, function calling)",
    )
    ai_model_lightweight: str = Field(
        default="qwen/qwen2.5-vl-3b-instruct:free",
        description="Lightweight AI model (3B, multimodal for examples)",
    )
    max_tokens_default: int = Field(default=1024, description="Default max tokens")
    max_tokens_feedback: int = Field(default=512, description="Max tokens for feedback")
    max_tokens_assessment: int = Field(default=256, description="Max tokens for assessment")
    temperature_default: float = Field(default=0.7, description="Default temperature")
    temperature_assessment: float = Field(default=0.3, description="Assessment temperature")
    temperature_feedback: float = Field(default=0.5, description="Feedback temperature")

    # Database
    database_url: str = Field(
        default="sqlite:///./data/promptheus.db",
        description="Database connection URL",
    )

    # Application
    environment: Literal["development", "production"] = Field(
        default="development",
        description="Application environment",
    )

    @computed_field
    @property
    def log_level(self) -> str:
        """Compute log level based on environment."""
        return "DEBUG" if self.environment == "development" else "WARNING"

    # Rate limiting
    rate_limit_requests: int = Field(default=10, description="Requests per minute per user")

    # Session
    session_timeout_minutes: int = Field(
        default=15,
        description="Session timeout in minutes",
    )

    # Bot Mode Configuration
    bot_mode: Literal["polling", "webhook"] = Field(
        default="polling",
        description="Bot operating mode: polling for development, webhook for production",
    )
    webhook_url: str | None = Field(
        default=None,
        description="Webhook URL for webhook mode (must be HTTPS)",
    )
    webhook_secret: str | None = Field(
        default=None,
        description="Webhook secret for request validation (recommended for security)",
    )
    webhook_port: int = Field(
        default=8443,
        description="Port for webhook HTTP server (must be 80, 88, 443, or 8443)",
    )
    webhook_path: str = Field(
        default="/webhook",
        description="Path for webhook endpoint",
    )

    # API Server (for health checks and future admin/user endpoints)
    api_server_enabled: bool = Field(
        default=True,
        description="Enable API server for health checks and future endpoints",
    )
    api_server_host: str = Field(
        default="0.0.0.0",
        description="Host for API server",
    )
    api_server_port: int = Field(
        default=8080,
        description="Port for API server",
    )
    health_check_timeout_seconds: int = Field(
        default=5,
        description="Timeout for health check operations in seconds",
    )

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Validate that webhook URL uses HTTPS protocol."""
        from promptheus.core.exceptions import ConfigurationError

        if v is not None and not v.startswith("https://"):
            raise ConfigurationError(
                f"Invalid webhook URL: must use HTTPS protocol, got '{v}'",
                details={"field": "webhook_url", "value": v, "required_protocol": "https"},
            )
        return v

    @field_validator("webhook_port")
    @classmethod
    def validate_webhook_port(cls, v: int) -> int:
        """Validate that webhook port is one of the allowed values."""
        from promptheus.core.exceptions import ConfigurationError

        allowed_ports = [80, 88, 443, 8443]
        if v not in allowed_ports:
            raise ConfigurationError(
                f"Invalid webhook port: must be one of {allowed_ports}, got {v}",
                details={"field": "webhook_port", "value": v, "allowed_ports": allowed_ports},
            )
        return v

    @field_validator("api_server_port")
    @classmethod
    def validate_api_server_port(cls, v: int) -> int:
        """Validate that API server port doesn't conflict with webhook port."""
        from promptheus.core.exceptions import ConfigurationError

        if v < 1 or v > 65535:
            raise ConfigurationError(
                f"Invalid API server port: must be between 1 and 65535, got {v}",
                details={"field": "api_server_port", "value": v, "valid_range": "1-65535"},
            )
        return v

    @model_validator(mode="after")
    def validate_webhook_mode_requirements(self) -> "Settings":
        """Validate that webhook mode has required configuration."""
        from promptheus.core.exceptions import ConfigurationError

        if self.bot_mode == "webhook" and not self.webhook_url:
            raise ConfigurationError(
                "Webhook mode requires webhook_url to be configured",
                details={"bot_mode": self.bot_mode, "webhook_url": self.webhook_url},
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
