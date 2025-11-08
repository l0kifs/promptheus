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

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Validate that webhook URL uses HTTPS protocol."""
        if v is not None and not v.startswith("https://"):
            raise ValueError("webhook_url must use HTTPS protocol")
        return v

    @field_validator("webhook_port")
    @classmethod
    def validate_webhook_port(cls, v: int) -> int:
        """Validate that webhook port is one of the allowed values."""
        allowed_ports = [80, 88, 443, 8443]
        if v not in allowed_ports:
            raise ValueError(f"webhook_port must be one of {allowed_ports}")
        return v

    @model_validator(mode="after")
    def validate_webhook_mode_requirements(self) -> "Settings":
        """Validate that webhook mode has required configuration."""
        if self.bot_mode == "webhook" and not self.webhook_url:
            raise ValueError("webhook_url is required when bot_mode is 'webhook'")
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
