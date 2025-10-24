"""
Logging infrastructure for CLI Navigation Tool.

Provides structured logging with performance metrics and user-friendly output
formatting for both development and production use.
"""

import sys
import json
import logging
import structlog
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

from src.exceptions import NavigationToolError


class NavigationLogger:
    """Enhanced logger with performance tracking and structured output."""

    def __init__(
        self,
        name: str = "nav_cli",
        level: str = "INFO",
        log_file: Optional[Path] = None,
        structured: bool = False,
        enable_performance: bool = True
    ):
        """Initialize the navigation logger."""
        self.name = name
        self.level = level.upper()
        self.log_file = log_file
        self.structured = structured
        self.enable_performance = enable_performance
        self.performance_data: Dict[str, Any] = {}
        self._setup_logging()

    def _setup_logging(self):
        """Configure structlog based on settings."""
        # Configure structlog processors
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
        ]

        if self.structured:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())

        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Configure standard logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, self.level)
        )

        # Add file handler if specified
        if self.log_file:
            self._setup_file_handler()

        # Set up our bound logger
        self.logger = structlog.get_logger(self.name)

    def _setup_file_handler(self):
        """Setup file logging with rotation."""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(getattr(logging, self.level))

            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)

            # Get root logger and add file handler
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)

        except Exception as e:
            # Fallback to console if file setup fails
            print(f"Warning: Could not setup file logging: {e}")

    @contextmanager
    def performance_timer(self, operation: str):
        """Context manager for timing operations."""
        if not self.enable_performance:
            yield
            return

        start_time = datetime.now()
        start_ms = self._get_timestamp_ms()

        self.logger.info(f"Starting {operation}", operation=operation)

        try:
            yield
        except Exception as e:
            duration_ms = self._get_timestamp_ms() - start_ms
            self.logger.error(
                f"Operation {operation} failed after {duration_ms}ms",
                operation=operation,
                duration_ms=duration_ms,
                error=str(e)
            )
            raise
        else:
            duration_ms = self._get_timestamp_ms() - start_ms
            self.performance_data[operation] = {
                "duration_ms": duration_ms,
                "timestamp": start_time.isoformat(),
                "success": True
            }

            self.logger.info(
                f"Completed {operation} in {duration_ms}ms",
                operation=operation,
                duration_ms=duration_ms
            )

    def log_user_interaction(self, action: str, query: str, details: Optional[Dict[str, Any]] = None):
        """Log user interaction events."""
        self.logger.info(
            f"User interaction: {action}",
            action=action,
            query=query,
            **(details or {})
        )

    def log_parsing_result(self, query: str, origin: str, destination: str, confidence: float, method: str):
        """Log location parsing results."""
        self.logger.info(
            "Location parsing completed",
            query=query,
            origin=origin,
            destination=destination,
            confidence_score=confidence,
            parsing_method=method
        )

    def log_browser_session(self, session_id: str, browser_type: str, launch_time_ms: int, url: Optional[str] = None):
        """Log browser session events."""
        details = {
            "session_id": session_id,
            "browser_type": browser_type,
            "launch_time_ms": launch_time_ms
        }
        if url:
            details["navigation_url"] = url

        self.logger.info(
            f"Browser session started with {browser_type}",
            **details
        )

    def log_navigation_result(self, success: bool, total_time_ms: int, url: Optional[str] = None,
                           error: Optional[str] = None):
        """Log navigation operation results."""
        details = {
            "success": success,
            "total_time_ms": total_time_ms
        }

        if url:
            details["navigation_url"] = url
        if error:
            details["error"] = error

        level = "info" if success else "error"
        getattr(self.logger, level)(
            f"Navigation {'completed' if success else 'failed'} in {total_time_ms}ms",
            **details
        )

    def log_error(self, error: NavigationToolError, context: str = "unknown"):
        """Log structured error information."""
        self.logger.error(
            f"Navigation error in {context}: {error.message}",
            context=context,
            error_code=error.error_code,
            error_details=error.details,
            suggestions=error.suggestions
        )

    def log_performance_summary(self):
        """Log a summary of all tracked performance data."""
        if not self.enable_performance or not self.performance_data:
            return

        total_time = sum(data["duration_ms"] for data in self.performance_data.values())

        self.logger.info(
            "Performance summary",
            total_tracked_time_ms=total_time,
            operations_count=len(self.performance_data),
            operations=self.performance_data
        )

    def get_performance_data(self) -> Dict[str, Any]:
        """Return collected performance data."""
        return self.performance_data.copy()

    def reset_performance_data(self):
        """Clear collected performance data."""
        self.performance_data.clear()

    @staticmethod
    def _get_timestamp_ms() -> int:
        """Get current timestamp in milliseconds."""
        return int(datetime.now().timestamp() * 1000)


# Global logger instance
_logger_instance: Optional[NavigationLogger] = None


def get_logger() -> NavigationLogger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = NavigationLogger()
    return _logger_instance


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False,
    enable_performance: bool = True
) -> NavigationLogger:
    """Setup the global logger with custom configuration."""
    global _logger_instance

    file_path = Path(log_file) if log_file else None
    _logger_instance = NavigationLogger(
        level=level,
        log_file=file_path,
        structured=structured,
        enable_performance=enable_performance
    )

    return _logger_instance


def log_user_message(message: str, level: str = "info"):
    """Log user-facing messages separately from technical logs."""
    logger = get_logger()

    # Always show user messages to console regardless of log level
    if level == "error":
        print(f"❌ {message}", file=sys.stderr)
    elif level == "warning":
        print(f"⚠️  {message}", file=sys.stderr)
    elif level == "success":
        print(f"✅ {message}", file=sys.stdout)
    else:
        print(f"ℹ️  {message}", file=sys.stdout)

    # Also log to the technical log
    getattr(logger.logger, level)(f"User message: {message}")


# Utility functions for common logging patterns
def log_query_start(query: str):
    """Log the start of query processing."""
    logger = get_logger()
    logger.log_user_interaction("query_start", query)
    log_user_message("正在解析位置信息...")


def log_parsing_success(origin: str, destination: str, confidence: float):
    """Log successful location parsing."""
    logger = get_logger()
    logger.log_parsing_result(
        query=f"{origin} to {destination}",
        origin=origin,
        destination=destination,
        confidence=confidence,
        method="hybrid_nlp"
    )
    log_user_message("位置信息解析完成")


def log_url_construction(url: str):
    """Log URL construction."""
    logger = get_logger()
    logger.logger.info("Navigation URL constructed", url=url)
    log_user_message("构建导航URL...")


def log_browser_launch(browser_type: str, session_id: str):
    """Log browser launch."""
    logger = get_logger()
    logger.log_browser_session(
        session_id=session_id,
        browser_type=browser_type,
        launch_time_ms=0  # Will be updated by performance timer
    )
    log_user_message("启动Chrome浏览器...")


def log_navigation_complete(total_time_ms: int, success: bool = True):
    """Log navigation completion."""
    logger = get_logger()
    logger.log_navigation_result(success=success, total_time_ms=total_time_ms)

    if success:
        log_user_message(f"路线规划成功！耗时 {total_time_ms}ms", "success")
    else:
        log_user_message("路线规划失败", "error")


def log_error_with_suggestions(error: NavigationToolError, context: str = "processing"):
    """Log error with user-friendly suggestions."""
    logger = get_logger()
    logger.log_error(error, context)

    # Log primary error message
    log_user_message(error.message, "error")

    # Log suggestions if available
    for suggestion in error.suggestions:
        log_user_message(f"💡 建议: {suggestion}", "info")

    # Log help text if available
    if error.help_text:
        log_user_message(error.help_text, "info")