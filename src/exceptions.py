"""
Custom exception classes for CLI Navigation Tool.

Provides specific exception types for different error scenarios in the navigation
processing pipeline, enabling better error handling and user feedback.
"""

from typing import Optional, Dict, Any, List


class NavigationToolError(Exception):
    """Base exception class for all navigation tool errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        help_text: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.suggestions = suggestions or []
        self.help_text = help_text
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured responses."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "suggestions": self.suggestions,
            "help_text": self.help_text,
            "details": self.details
        }


class BrowserNotAvailableError(NavigationToolError):
    """Raised when Chrome/Chromium browser is not available on the system."""

    def __init__(self, browser_type: str = "Chrome/Chromium"):
        message = f"{browser_type} browser not found on this system"
        super().__init__(
            message=message,
            error_code="BROWSER_NOT_AVAILABLE",
            suggestions=[
                "Install Google Chrome from https://www.google.com/chrome/",
                "Install Chromium from your system package manager",
                "For macOS: brew install --cask chromium",
                "For Ubuntu: sudo apt-get install chromium-browser",
                "For Windows: Download and install Chrome from google.com"
            ],
            help_text="Chrome/Chromium browser is required for navigation functionality. "
                     "Please install one of the supported browsers and try again."
        )


class LocationParsingError(NavigationToolError):
    """Raised when natural language location parsing fails."""

    def __init__(
        self,
        input_text: str,
        reason: str = "Unable to parse location information",
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to parse locations from: '{input_text[:50]}...'"
        super().__init__(
            message=message,
            error_code="PARSE_ERROR",
            suggestions=[
                "Use format: '从[起点]到[终点]' (e.g., '从北京到上海')",
                "Include specific city names: '北京站到首都机场'",
                "Use landmark names: '天安门到故宫'",
                "Check for proper Chinese characters",
                "Keep the query simple and clear"
            ],
            help_text="Please use the format '从[起点]到[终点]' with clear location names.",
            details={"input_text": input_text, "parsing_reason": reason, **(details or {})}
        )


class NavigationError(NavigationToolError):
    """Raised when navigation or browser automation fails."""

    def __init__(
        self,
        operation: str,
        reason: str = "Navigation operation failed",
        url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Navigation failed during {operation}: {reason}"
        super().__init__(
            message=message,
            error_code="NAVIGATION_ERROR",
            suggestions=[
                "Check your internet connection",
                "Try again with different locations",
                "Clear browser cache and restart",
                "Ensure Chrome/Chromium is not blocked by firewall",
                "Try using a different transport mode"
            ],
            help_text="Navigation operation encountered an error. Please check your connection "
                     "and try again.",
            details={"operation": operation, "url": url, **(details or {})}
        )


class NetworkError(NavigationToolError):
    """Raised when network connectivity issues occur."""

    def __init__(self, operation: str, reason: str = "Network connection failed"):
        message = f"Network error during {operation}: {reason}"
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            suggestions=[
                "Check your internet connection",
                "Try switching to a different network",
                "Disable VPN if enabled",
                "Check firewall settings",
                "Try again after a few seconds"
            ],
            help_text="Network connectivity issue detected. Please check your connection "
                     "and try again."
        )


class TimeoutError(NavigationToolError):
    """Raised when operations exceed the timeout limit."""

    def __init__(
        self,
        operation: str,
        timeout_seconds: int,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            suggestions=[
                "Try again with a faster internet connection",
                "Close other applications to free up system resources",
                "Use more specific location names",
                "Check if Chrome/Chromium is running slowly"
            ],
            help_text=f"Operation exceeded the {timeout_seconds}-second time limit. "
                     "Please try again with better system conditions.",
            details={"timeout_seconds": timeout_seconds, **(details or {})}
        )


class ConfigurationError(NavigationToolError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, config_key: str, reason: str = "Invalid configuration"):
        message = f"Configuration error for '{config_key}': {reason}"
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            suggestions=[
                "Check your .env file for correct values",
                "Copy .env.example to .env and fill in required values",
                "Ensure API keys are valid and have required permissions",
                "Check environment variable spelling"
            ],
            help_text="Please check your configuration file (.env) and ensure all required "
                     "settings are properly configured."
        )


class ValidationError(NavigationToolError):
    """Raised when input validation fails."""

    def __init__(
        self,
        field_name: str,
        value: str,
        reason: str = "Invalid input"
    ):
        message = f"Validation failed for {field_name}: {reason}"
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            suggestions=[
                "Check input length (3-200 characters required)",
                "Ensure both origin and destination are provided",
                "Use proper Chinese characters for locations",
                "Avoid special characters in location names"
            ],
            help_text="Input validation failed. Please check your query format and try again.",
            details={"field_name": field_name, "invalid_value": value}
        )


class CacheError(NavigationToolError):
    """Raised when cache operations fail."""

    def __init__(self, operation: str, reason: str = "Cache operation failed"):
        message = f"Cache error during {operation}: {reason}"
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            suggestions=[
                "Clear cache and try again",
                "Check available disk space",
                "Verify file permissions for cache directory",
                "Disable caching temporarily"
            ],
            help_text="Cache operation encountered an error. This may affect performance "
                     "but should not prevent normal operation."
        )


class LLMError(NavigationToolError):
    """Raised when LLM API calls fail."""

    def __init__(
        self,
        provider: str,
        reason: str = "LLM API call failed",
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"LLM API error with {provider}: {reason}"
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            suggestions=[
                "Check your API key configuration",
                "Verify API key has sufficient quota",
                "Try switching to a different LLM provider",
                "Check API service status",
                "Try again after a few seconds"
            ],
            help_text="Language model API error. Please check your configuration and try again.",
            details={"provider": provider, **(details or {})}
        )


class BrowserLaunchError(NavigationToolError):
    """Raised when browser launch fails specifically."""

    def __init__(
        self,
        browser_type: str,
        reason: str = "Browser launch failed",
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to launch {browser_type}: {reason}"
        super().__init__(
            message=message,
            error_code="BROWSER_LAUNCH_ERROR",
            suggestions=[
                "Install Playwright browsers: playwright install chromium",
                "Check system permissions for browser launch",
                "Close existing browser instances",
                "Ensure sufficient system memory available",
                "Try running with different browser settings"
            ],
            help_text="Browser launch failed. Please check Playwright installation and system permissions.",
            details={"browser_type": browser_type, **(details or {})}
        )


# Exception handling utility functions
def handle_unexpected_error(error: Exception, context: str = "unknown") -> NavigationToolError:
    """Convert unexpected exceptions to NavigationToolError."""
    if isinstance(error, NavigationToolError):
        return error

    # Handle common Python exceptions
    if isinstance(error, ValueError):
        return ValidationError(
            field_name="unknown",
            value=str(error),
            reason=f"Value error in {context}: {str(error)}"
        )
    elif isinstance(error, ConnectionError):
        return NetworkError(operation=context, reason=str(error))
    elif isinstance(error, TimeoutError):
        return TimeoutError(operation=context, timeout_seconds=0)
    else:
        return NavigationToolError(
            message=f"Unexpected error in {context}: {str(error)}",
            error_code="SYSTEM_ERROR",
            suggestions=[
                "Try again with different input",
                "Check system resources",
                "Report this issue if it persists"
            ],
            help_text="An unexpected error occurred. Please try again or report the issue.",
            details={"original_error": str(error), "context": context}
        )