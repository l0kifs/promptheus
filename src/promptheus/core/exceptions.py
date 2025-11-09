"""Domain-specific exceptions for Promptheus application."""

from typing import Any


class PromptheusError(Exception):
    """Base exception for all Promptheus errors.

    All custom exceptions should inherit from this base class
    to provide consistent error handling and logging.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize Promptheus error.

        Args:
            message: Human-readable error message
            details: Additional error details for debugging/logging
        """
        super().__init__(message)
        self.details = details or {}


class ValidationError(PromptheusError):
    """Raised when input validation fails.

    Used for validating user inputs, configuration values,
    and business rule constraints.
    """

    pass


class BusinessError(PromptheusError):
    """Raised when business rules are violated.

    Used for domain-specific business logic violations
    that are not input validation errors.
    """

    pass


class SystemError(PromptheusError):
    """Raised when system-level errors occur.

    Used for internal errors, database failures,
    external service issues, etc.
    """

    pass


class ConfigurationError(ValidationError):
    """Raised when configuration validation fails.

    Used specifically for settings and configuration
    validation errors.
    """

    pass


class AssessmentError(BusinessError):
    """Raised when assessment operations fail.

    Used for errors related to skill assessment,
    question validation, and evaluation processes.
    """

    pass


class DatabaseError(SystemError):
    """Raised when database operations fail.

    Used for connection issues, constraint violations,
    and other database-related errors.
    """

    pass


class AIError(SystemError):
    """Raised when AI service operations fail.

    Used for OpenRouter API errors, model failures,
    and AI-related processing issues.
    """

    pass
