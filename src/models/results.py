"""
Result-related data models for CLI Navigation Tool.

Contains ProcessingResult model and result-related utilities for
structured responses and user feedback.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models.navigation import NavigationQuery, RouteParameters, BrowserSession


class ResultStatus(str, Enum):
    """Status of processing results."""
    SUCCESS = "success"
    PARSE_ERROR = "parse_error"
    BROWSER_ERROR = "browser_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    USER_ERROR = "user_error"
    SYSTEM_ERROR = "system_error"
    VALIDATION_ERROR = "validation_error"


class ResultSeverity(str, Enum):
    """Severity level for results."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ProcessingResult(BaseModel):
    """Complete result of processing a navigation query."""

    # Result status and success
    status: ResultStatus = Field(..., description="Overall processing status")
    success: bool = Field(..., description="Whether processing was successful")
    message: str = Field(..., description="Human-readable result message")
    severity: ResultSeverity = Field(ResultSeverity.INFO, description="Result severity level")

    # Processing chain components
    query: Optional[NavigationQuery] = Field(None, description="Parsed navigation query")
    route_params: Optional[RouteParameters] = Field(None, description="Route parameters")
    browser_session: Optional[BrowserSession] = Field(None, description="Browser session info")

    # Performance metrics
    total_time_ms: int = Field(0, ge=0, description="Total processing time in ms")
    component_times: Dict[str, int] = Field(default_factory=dict, description="Component processing times")

    # Error details
    error_type: Optional[str] = Field(None, description="Type of error if failed")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error information")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")

    # User guidance
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for user")
    help_text: Optional[str] = Field(None, description="Additional help text")
    next_actions: List[str] = Field(default_factory=list, description="Suggested next actions")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Result timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    debug_info: Dict[str, Any] = Field(default_factory=dict, description="Debug information")

    @validator('total_time_ms')
    def validate_performance(cls, v):
        """Validate that processing time meets 10-second target."""
        if v > 10000:  # 10 seconds per clarification
            raise ValueError("Processing time exceeds 10 second limit")
        return v

    @validator('suggestions')
    def validate_suggestions(cls, v):
        """Validate suggestions list."""
        if len(v) > 10:
            raise ValueError("Too many suggestions (maximum 10)")
        return v

    def meets_performance_target(self) -> bool:
        """Check if result meets 10-second performance target."""
        return self.total_time_ms <= 10000

    def get_user_message(self) -> str:
        """Get user-friendly message based on result status."""
        if self.success:
            if self.total_time_ms < 1000:
                return f"✅ 路线规划成功！耗时 {self.total_time_ms}ms"
            elif self.total_time_ms < 5000:
                return f"✅ 路线规划完成，耗时 {self.total_time_ms}ms"
            elif self.total_time_ms < 8000:
                return f"✅ 路线规划成功，耗时 {self.total_time_ms}ms"
            else:
                return f"⚠️ 路线规划成功，但耗时较长 ({self.total_time_ms}ms)"
        else:
            return f"❌ {self.message}"

    def get_severity_color(self) -> str:
        """Get color code for severity level."""
        colors = {
            ResultSeverity.INFO: "green",
            ResultSeverity.WARNING: "yellow",
            ResultSeverity.ERROR: "red",
            ResultSeverity.CRITICAL: "red"
        }
        return colors.get(self.severity, "white")

    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion to the result."""
        if suggestion not in self.suggestions:
            self.suggestions.append(suggestion)

    def add_next_action(self, action: str) -> None:
        """Add a suggested next action."""
        if action not in self.next_actions:
            self.next_actions.append(action)

    def set_error(self, error_type: str, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Set error information on the result."""
        self.success = False
        self.status = ResultStatus.ERROR
        self.error_type = error_type
        self.message = message
        self.error_code = error_code or error_type.upper()
        self.error_details = details or {}

        # Set severity based on error type
        if error_type in ["system_error", "timeout_error", "critical_error"]:
            self.severity = ResultSeverity.CRITICAL
        elif error_type in ["parse_error", "browser_error"]:
            self.severity = ResultSeverity.ERROR
        else:
            self.severity = ResultSeverity.WARNING

    def mark_success(self, message: Optional[str] = None) -> None:
        """Mark result as successful."""
        self.success = True
        self.status = ResultStatus.SUCCESS
        self.severity = ResultSeverity.INFO
        if message:
            self.message = message
        elif not self.message:
            self.message = "Operation completed successfully"

    def set_timing(self, component: str, time_ms: int) -> None:
        """Set timing for a specific component."""
        self.component_times[component] = time_ms

    def get_component_breakdown(self) -> str:
        """Get formatted breakdown of component times."""
        if not self.component_times:
            return "No component timing data available"

        breakdown = []
        for component, time_ms in self.component_times.items():
            breakdown.append(f"{component}: {time_ms}ms")

        return " | ".join(breakdown)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "status": self.status.value,
            "success": self.success,
            "message": self.message,
            "severity": self.severity.value,
            "query": self.query.to_dict() if self.query else None,
            "route_params": self.route_params.to_dict() if self.route_params else None,
            "browser_session": self.browser_session.to_dict() if self.browser_session else None,
            "total_time_ms": self.total_time_ms,
            "component_times": self.component_times,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "error_details": self.error_details,
            "suggestions": self.suggestions,
            "help_text": self.help_text,
            "next_actions": self.next_actions,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
            "debug_info": self.debug_info
        }


class ValidationResult(BaseModel):
    """Validation result for input and configuration."""

    is_valid: bool = Field(..., description="Whether validation passed")
    message: str = Field(..., description="Validation message")
    field_name: Optional[str] = Field(None, description="Field that failed validation")
    value: Optional[str] = Field(None, description="The invalid value")
    expected_format: Optional[str] = Field(None, description="Expected format")
    suggestions: List[str] = Field(default_factory=list, description="Validation suggestions")

    def __bool__(self) -> bool:
        """Allow ValidationResult to be used in boolean context."""
        return self.is_valid


class ProgressUpdate(BaseModel):
    """Progress update for long-running operations."""

    operation: str = Field(..., description="Operation being performed")
    progress_percent: int = Field(0, ge=0, le=100, description="Progress percentage (0-100)")
    message: str = Field(..., description="Progress message")
    current_step: str = Field(..., description="Current step being performed")
    total_steps: Optional[int] = Field(None, description="Total number of steps")
    estimated_remaining_seconds: Optional[int] = Field(None, description="Estimated remaining time")

    def to_dict(self) -> Dict[str, Any]:
        """Convert progress update to dictionary."""
        return {
            "operation": self.operation,
            "progress_percent": self.progress_percent,
            "message": self.message,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "estimated_remaining_seconds": self.estimated_remaining_seconds
        }


# Result creation utilities
def create_success_result(
    message: str,
    query: Optional[NavigationQuery] = None,
    route_params: Optional[RouteParameters] = None,
    browser_session: Optional[BrowserSession] = None,
    total_time_ms: int = 0,
    component_times: Optional[Dict[str, int]] = None
) -> ProcessingResult:
    """Create a successful processing result."""
    return ProcessingResult(
        status=ResultStatus.SUCCESS,
        success=True,
        message=message,
        severity=ResultSeverity.INFO,
        query=query,
        route_params=route_params,
        browser_session=browser_session,
        total_time_ms=total_time_ms,
        component_times=component_times or {}
    )


def create_error_result(
    error_type: str,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None
) -> ProcessingResult:
    """Create an error processing result."""
    result = ProcessingResult(
        status=ResultStatus.ERROR,
        success=False,
        message=message,
        error_type=error_type,
        error_code=error_code or error_type.upper(),
        error_details=details or {}
    )

    if suggestions:
        result.suggestions = suggestions

    return result


def create_timeout_result(
    operation: str,
    timeout_seconds: int,
    message: Optional[str] = None
) -> ProcessingResult:
    """Create a timeout processing result."""
    timeout_msg = message or f"Operation '{operation}' timed out after {timeout_seconds} seconds"

    return ProcessingResult(
        status=ResultStatus.TIMEOUT_ERROR,
        success=False,
        message=timeout_msg,
        error_type="timeout_error",
        error_code="TIMEOUT",
        error_details={"operation": operation, "timeout_seconds": timeout_seconds},
        suggestions=[
            "Try again with better network connection",
            "Check if system resources are available",
            "Consider increasing timeout settings"
        ]
    )


def create_parse_error_result(
    input_text: str,
    reason: str,
    suggestions: Optional[List[str]] = None
) -> ProcessingResult:
    """Create a parse error processing result."""
    parse_msg = f"Failed to parse navigation query: {reason}"

    default_suggestions = [
        "Use format: '从[起点]到[终点]'",
        "Example: '从北京到上海'",
        "Ensure location names are in Chinese"
    ]

    return ProcessingResult(
        status=ResultStatus.PARSE_ERROR,
        success=False,
        message=parse_msg,
        error_type="parse_error",
        error_code="PARSE_FAILED",
        error_details={"input_text": input_text, "reason": reason},
        suggestions=suggestions or default_suggestions
    )


def create_browser_error_result(
    browser_type: str,
    reason: str,
    suggestions: Optional[List[str]] = None
) -> ProcessingResult:
    """Create a browser error processing result."""
    browser_msg = f"Browser error with {browser_type}: {reason}"

    default_suggestions = [
        "Ensure Chrome/Chromium is installed",
        "Check browser permissions",
        "Try running with administrator privileges"
    ]

    return ProcessingResult(
        status=ResultStatus.BROWSER_ERROR,
        success=False,
        message=browser_msg,
        error_type="browser_error",
        error_code="BROWSER_FAILED",
        error_details={"browser_type": browser_type, "reason": reason},
        suggestions=suggestions or default_suggestions
    )