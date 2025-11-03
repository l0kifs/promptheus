"""Application settings using Pydantic."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
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

    # Model parameters
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
    log_level: str = Field(default="INFO", description="Logging level")

    # Rate limiting
    rate_limit_requests: int = Field(default=10, description="Requests per minute per user")

    # Session
    session_timeout_minutes: int = Field(
        default=15,
        description="Session timeout in minutes",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
