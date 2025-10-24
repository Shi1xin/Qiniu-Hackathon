"""
Browser-related data models for CLI Navigation Tool.

Contains BrowserSession model and browser-related enums for
Playwright integration and browser state management.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class BrowserType(str, Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserStatus(str, Enum):
    """Browser session status."""
    LAUNCHING = "launching"
    READY = "ready"
    NAVIGATING = "navigating"
    ERROR = "error"
    CLOSED = "closed"


class BrowserSession(BaseModel):
    """Represents a browser session state and configuration."""

    # Basic session information
    session_id: str = Field(..., description="Unique session identifier")
    browser_type: BrowserType = Field(BrowserType.CHROMIUM, description="Type of browser")
    status: BrowserStatus = Field(BrowserStatus.LAUNCHING, description="Current browser status")

    # Browser configuration
    headless: bool = Field(False, description="Run browser in headless mode")
    user_agent: Optional[str] = Field(None, description="Custom user agent string")
    window_size: Dict[str, int] = Field(
        default={"width": 1280, "height": 800},
        description="Browser window dimensions"
    )

    # Session state
    launched_at: Optional[datetime] = Field(None, description="Session launch timestamp")
    page_url: Optional[str] = Field(None, description="Current page URL")
    page_title: Optional[str] = Field(None, description="Current page title")

    # Performance metrics
    launch_time_ms: int = Field(0, ge=0, description="Browser launch time in ms")
    navigation_time_ms: int = Field(0, ge=0, description="Page navigation time in ms")
    total_time_ms: int = Field(0, ge=0, description="Total session time in ms")

    # Error handling
    launch_errors: list[str] = Field(default_factory=list, description="Errors during launch")
    navigation_errors: list[str] = Field(default_factory=list, description="Errors during navigation")
    last_error: Optional[str] = Field(None, description="Most recent error")

    # Browser-specific settings
    ignore_https_errors: bool = Field(False, description="Ignore HTTPS certificate errors")
    disable_web_security: bool = Field(False, description="Disable web security features")
    enable_javascript: bool = Field(True, description="Enable JavaScript execution")

    def __init__(self, **data):
        """Initialize with a unique session ID if not provided."""
        if 'session_id' not in data:
            data['session_id'] = str(uuid.uuid4())
        super().__init__(**data)

    @validator('window_size')
    def validate_window_size(cls, v):
        """Validate window size dimensions."""
        if not isinstance(v, dict):
            raise ValueError("Window size must be a dictionary")

        if 'width' not in v or 'height' not in v:
            raise ValueError("Window size must include 'width' and 'height'")

        width = v.get('width', 0)
        height = v.get('height', 0)

        if width < 800 or width > 1920:
            raise ValueError("Window width must be between 800 and 1920")
        if height < 600 or height > 1080:
            raise ValueError("Window height must be between 600 and 1080")

        return v

    def is_active(self) -> bool:
        """Check if browser session is active."""
        return self.status in [BrowserStatus.READY, BrowserStatus.NAVIGATING]

    def is_ready(self) -> bool:
        """Check if browser is ready for operations."""
        return self.status == BrowserStatus.READY

    def is_error(self) -> bool:
        """Check if browser session has errors."""
        return self.status == BrowserStatus.ERROR

    def is_closed(self) -> bool:
        """Check if browser session is closed."""
        return self.status == BrowserStatus.CLOSED

    def get_total_time_ms(self) -> int:
        """Get total session time including launch and navigation."""
        return self.launch_time_ms + self.navigation_time_ms

    def mark_ready(self) -> None:
        """Mark browser as ready."""
        self.status = BrowserStatus.READY
        if self.launched_at is None:
            self.launched_at = datetime.now()

    def mark_navigating(self, url: str) -> None:
        """Mark browser as navigating to a URL."""
        self.status = BrowserStatus.NAVIGATING
        self.page_url = url

    def mark_navigation_complete(self, url: str, title: Optional[str] = None, time_ms: int = 0) -> None:
        """Mark navigation as complete."""
        self.status = BrowserStatus.READY
        self.page_url = url
        self.page_title = title
        self.navigation_time_ms = time_ms
        self.total_time_ms = self.launch_time_ms + time_ms

    def mark_error(self, error: str) -> None:
        """Mark browser session as having an error."""
        self.status = BrowserStatus.ERROR
        self.last_error = error

    def add_launch_error(self, error: str) -> None:
        """Add an error that occurred during launch."""
        self.launch_errors.append(error)
        self.mark_error(error)

    def add_navigation_error(self, error: str) -> None:
        """Add an error that occurred during navigation."""
        self.navigation_errors.append(error)
        self.mark_error(error)

    def mark_closed(self) -> None:
        """Mark browser session as closed."""
        self.status = BrowserStatus.CLOSED

    def to_dict(self) -> Dict[str, Any]:
        """Convert browser session to dictionary."""
        return {
            "session_id": self.session_id,
            "browser_type": self.browser_type.value,
            "status": self.status.value,
            "headless": self.headless,
            "user_agent": self.user_agent,
            "window_size": self.window_size,
            "launched_at": self.launched_at.isoformat() if self.launched_at else None,
            "page_url": self.page_url,
            "page_title": self.page_title,
            "launch_time_ms": self.launch_time_ms,
            "navigation_time_ms": self.navigation_time_ms,
            "total_time_ms": self.get_total_time_ms(),
            "launch_errors": self.launch_errors,
            "navigation_errors": self.navigation_errors,
            "last_error": self.last_error,
            "ignore_https_errors": self.ignore_https_errors,
            "disable_web_security": self.disable_web_security,
            "enable_javascript": self.enable_javascript
        }


class BrowserPool(BaseModel):
    """Manages a pool of browser sessions for performance optimization."""

    max_sessions: int = Field(3, ge=1, le=10, description="Maximum concurrent browser sessions")
    session_timeout_minutes: int = Field(5, ge=1, le=60, description="Session timeout in minutes")
    enable_connection_pooling: bool = Field(True, description="Enable connection pooling")

    def __init__(self, **data):
        """Initialize browser pool."""
        super().__init__(**data)
        self.active_sessions: Dict[str, BrowserSession] = {}
        self.available_sessions: list[str] = []