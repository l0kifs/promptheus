"""Tests for custom exception classes."""

from promptheus.core.exceptions import (
    AIError,
    AssessmentError,
    BusinessError,
    ConfigurationError,
    DatabaseError,
    PromptheusError,
    SystemError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy and inheritance."""

    def test_base_exception_creation(self):
        """Test that base exception can be created with message and details."""
        error = PromptheusError("Test message", details={"key": "value"})
        assert str(error) == "Test message"
        assert error.details == {"key": "value"}

    def test_base_exception_without_details(self):
        """Test that base exception works without details."""
        error = PromptheusError("Test message")
        assert str(error) == "Test message"
        assert error.details == {}

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from PromptheusError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, ValidationError)
        assert isinstance(error, PromptheusError)
        assert isinstance(error, Exception)

    def test_business_error_inheritance(self):
        """Test that BusinessError inherits from PromptheusError."""
        error = BusinessError("Business rule violated")
        assert isinstance(error, BusinessError)
        assert isinstance(error, PromptheusError)
        assert isinstance(error, Exception)

    def test_system_error_inheritance(self):
        """Test that SystemError inherits from PromptheusError."""
        error = SystemError("System error occurred")
        assert isinstance(error, SystemError)
        assert isinstance(error, PromptheusError)
        assert isinstance(error, Exception)

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from ValidationError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, ValidationError)
        assert isinstance(error, PromptheusError)
        assert isinstance(error, Exception)

    def test_assessment_error_inheritance(self):
        """Test that AssessmentError inherits from BusinessError."""
        error = AssessmentError("Assessment failed")
        assert isinstance(error, AssessmentError)
        assert isinstance(error, BusinessError)
        assert isinstance(error, PromptheusError)
        assert isinstance(error, Exception)

    def test_database_error_inheritance(self):
        """Test that DatabaseError inherits from SystemError."""
        error = DatabaseError("Database error")
        assert isinstance(error, DatabaseError)
        assert isinstance(error, SystemError)
        assert isinstance(error, PromptheusError)
        assert isinstance(error, Exception)

    def test_ai_error_inheritance(self):
        """Test that AIError inherits from SystemError."""
        error = AIError("AI service error")
        assert isinstance(error, AIError)
        assert isinstance(error, SystemError)
        assert isinstance(error, PromptheusError)
        assert isinstance(error, Exception)


class TestExceptionDetails:
    """Test exception details functionality."""

    def test_validation_error_with_details(self):
        """Test ValidationError with detailed information."""
        details = {
            "field": "skill_level",
            "value": "invalid",
            "expected": ["beginner", "intermediate", "advanced"],
        }
        error = ValidationError("Invalid skill level", details=details)
        assert error.details == details
        assert str(error) == "Invalid skill level"

    def test_configuration_error_with_details(self):
        """Test ConfigurationError with detailed information."""
        details = {
            "field": "webhook_url",
            "value": "http://example.com",
            "required_protocol": "https",
        }
        error = ConfigurationError("Invalid webhook URL protocol", details=details)
        assert error.details == details

    def test_assessment_error_with_details(self):
        """Test AssessmentError with detailed information."""
        details = {"expected": 5, "actual": 3, "missing_questions": 2}
        error = AssessmentError("Invalid assessment configuration", details=details)
        assert error.details == details

    def test_system_error_with_details(self):
        """Test SystemError with detailed information."""
        details = {"component": "database", "operation": "connect", "error_code": "ECONNREFUSED"}
        error = SystemError("Database connection failed", details=details)
        assert error.details == details


class TestExceptionMessages:
    """Test exception message formatting."""

    def test_descriptive_messages(self):
        """Test that exceptions provide descriptive error messages."""
        # Validation errors
        assert str(ValidationError("Field is required")) == "Field is required"
        assert str(ConfigurationError("Invalid configuration")) == "Invalid configuration"

        # Business errors
        assert str(BusinessError("Business rule violated")) == "Business rule violated"
        assert (
            str(AssessmentError("Assessment validation failed")) == "Assessment validation failed"
        )

        # System errors
        assert str(SystemError("Internal error")) == "Internal error"
        assert str(DatabaseError("Connection failed")) == "Connection failed"
        assert str(AIError("AI service unavailable")) == "AI service unavailable"
