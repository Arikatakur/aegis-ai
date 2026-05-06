"""Custom exceptions for Aegis AI."""


class AegisError(Exception):
    """Base exception for all Aegis AI errors."""


class TargetDownError(AegisError):
    """Raised when the target LLM endpoint is unreachable or returns a connection error."""


class RateLimitError(AegisError):
    """Raised when the target responds with HTTP 429 Too Many Requests."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: float = 0.0) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class InvalidTargetResponseError(AegisError):
    """Raised when the target returns an unexpected or malformed response."""


class ConfigurationError(AegisError):
    """Raised when the Aegis configuration is invalid or incomplete."""


class ValidationError(AegisError):
    """Raised when result validation encounters an unrecoverable error."""


class TemplateLoadError(AegisError):
    """Raised when an attack template JSON file cannot be loaded or parsed."""
