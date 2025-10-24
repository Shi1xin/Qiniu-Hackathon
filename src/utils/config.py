"""
Configuration management for CLI Navigation Tool.

Uses Pydantic Settings for type-safe configuration with environment variable
support and validation.
"""

from typing import Optional, List, Literal
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pydantic.types import PositiveInt


class NavigationConfig(BaseSettings):
    """Configuration settings for the navigation tool."""

    # LLM Configuration
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")

    # Browser Configuration
    default_browser: Literal["chromium"] = Field("chromium", env="NAV_TOOL_DEFAULT_BROWSER")
    headless_mode: bool = Field(False, env="NAV_TOOL_HEADLESS_MODE")
    window_size: str = Field("1280,800", env="NAV_TOOL_WINDOW_SIZE")
    user_agent: Optional[str] = Field(None, env="NAV_TOOL_USER_AGENT")

    # Performance Configuration
    timeout_ms: PositiveInt = Field(10000, env="NAV_TOOL_TIMEOUT_MS")
    browser_timeout_ms: PositiveInt = Field(5000, env="NAV_TOOL_BROWSER_TIMEOUT_MS")
    network_timeout_ms: PositiveInt = Field(3000, env="NAV_TOOL_NETWORK_TIMEOUT_MS")
    enable_profiling: bool = Field(False, env="NAV_TOOL_ENABLE_PROFILING")
    profile_dir: Optional[str] = Field("/tmp/nav_cli_profile", env="NAV_TOOL_PROFILE_DIR")

    # Cache Configuration
    enable_cache: bool = Field(True, env="NAV_TOOL_ENABLE_CACHE")
    cache_ttl: PositiveInt = Field(3600, env="NAV_TOOL_CACHE_TTL")  # seconds
    cache_dir: str = Field("/tmp/nav_cli_cache", env="NAV_TOOL_CACHE_DIR")
    cache_max_size: PositiveInt = Field(100, env="NAV_TOOL_CACHE_MAX_SIZE")  # MB

    # Map Service Configuration
    map_provider: Literal["gaode", "baidu", "tencent"] = Field("gaode", env="NAV_TOOL_MAP_PROVIDER")
    fallback_provider: Literal["gaode", "baidu", "tencent"] = Field("baidu", env="NAV_TOOL_FALLBACK_PROVIDER")
    transport_mode: Literal["car", "walk", "bus", "ride", "truck"] = Field("car", env="NAV_TOOL_TRANSPORT_MODE")
    avoid_tolls: bool = Field(False, env="NAV_TOOL_AVOID_TOLLS")
    avoid_highways: bool = Field(False, env="NAV_TOOL_AVOID_HIGHWAYS")

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field("INFO", env="NAV_TOOL_LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="NAV_TOOL_LOG_FILE")
    structured_logging: bool = Field(False, env="NAV_TOOL_STRUCTURED_LOGGING")
    log_performance: bool = Field(True, env="NAV_TOOL_LOG_PERFORMANCE")

    # Debug Configuration
    debug: bool = Field(False, env="NAV_TOOL_DEBUG")
    debug_keep_browser: bool = Field(False, env="NAV_TOOL_DEBUG_KEEP_BROWSER")
    verbose_agent: bool = Field(False, env="NAV_TOOL_VERBOSE_AGENT")
    debug_network: bool = Field(False, env="NAV_TOOL_DEBUG_NETWORK")

    # Advanced Configuration
    max_retries: int = Field(1, ge=0, le=3, env="NAV_TOOL_MAX_RETRIES")
    retry_delay_ms: PositiveInt = Field(1000, env="NAV_TOOL_RETRY_DELAY_MS")
    enable_disambiguation: bool = Field(True, env="NAV_TOOL_ENABLE_DISAMIGUATION")
    preferred_city: Optional[str] = Field(None, env="NAV_TOOL_PREFERRED_CITY")
    language: Literal["zh-CN", "en-US"] = Field("zh-CN", env="NAV_TOOL_LANGUAGE")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"  # Allow extra fields for environment variables
    }

    @field_validator('window_size')
    @classmethod
    def parse_window_size(cls, v):
        """Parse window size string 'width,height' into tuple."""
        try:
            width, height = map(int, v.split(','))
            if width < 800 or width > 1920:
                raise ValueError("Window width must be between 800 and 1920")
            if height < 600 or height > 1080:
                raise ValueError("Window height must be between 600 and 1080")
            return v
        except (ValueError, AttributeError):
            raise ValueError("Window size must be in format 'width,height' (e.g., '1280,800')")

    @field_validator('profile_dir', 'cache_dir')
    @classmethod
    def create_directories(cls, v):
        """Ensure directories exist."""
        if v:
            Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @field_validator('timeout_ms', 'browser_timeout_ms', 'network_timeout_ms')
    @classmethod
    def validate_timeouts(cls, v):
        """Ensure timeout values are reasonable."""
        if v > 60000:  # 1 minute
            raise ValueError("Timeout values should not exceed 60 seconds")
        if v < 1000:  # 1 second
            raise ValueError("Timeout values should be at least 1 second")
        return v

    @field_validator('fallback_provider')
    @classmethod
    def different_fallback_provider(cls, v, info):
        """Ensure fallback provider is different from primary."""
        if info.data and 'map_provider' in info.data and v == info.data['map_provider']:
            raise ValueError("Fallback provider must be different from primary provider")
        return v

    @field_validator('cache_ttl')
    @classmethod
    def reasonable_cache_ttl(cls, v):
        """Ensure cache TTL is reasonable."""
        if v > 86400:  # 24 hours
            raise ValueError("Cache TTL should not exceed 24 hours")
        if v < 60:  # 1 minute
            raise ValueError("Cache TTL should be at least 1 minute")
        return v

    def get_window_dimensions(self) -> tuple[int, int]:
        """Get window size as (width, height) tuple."""
        width, height = map(int, self.window_size.split(','))
        return width, height

    def has_llm_config(self) -> bool:
        """Check if any LLM API key is configured."""
        return any([
            self.google_api_key,
            self.openai_api_key,
            self.anthropic_api_key
        ])

    def get_primary_llm_provider(self) -> Optional[str]:
        """Get the primary LLM provider based on available API keys."""
        if self.google_api_key:
            return "google"
        elif self.openai_api_key:
            return "openai"
        elif self.anthropic_api_key:
            return "anthropic"
        else:
            return None

    def get_debug_config(self) -> dict:
        """Get all debug-related settings as a dictionary."""
        return {
            "debug": self.debug,
            "debug_keep_browser": self.debug_keep_browser,
            "verbose_agent": self.verbose_agent,
            "debug_network": self.debug_network,
            "enable_profiling": self.enable_profiling
        }

    def get_browser_config(self) -> dict:
        """Get browser-related settings as a dictionary."""
        width, height = self.get_window_dimensions()
        return {
            "browser_type": self.default_browser,
            "headless": self.headless_mode,
            "window_size": {"width": width, "height": height},
            "user_agent": self.user_agent,
            "timeout_ms": self.browser_timeout_ms
        }

    def get_cache_config(self) -> dict:
        """Get cache-related settings as a dictionary."""
        return {
            "enabled": self.enable_cache,
            "ttl_seconds": self.cache_ttl,
            "directory": self.cache_dir,
            "max_size_mb": self.cache_max_size
        }

    def get_map_config(self) -> dict:
        """Get map service settings as a dictionary."""
        return {
            "primary_provider": self.map_provider,
            "fallback_provider": self.fallback_provider,
            "transport_mode": self.transport_mode,
            "avoid_tolls": self.avoid_tolls,
            "avoid_highways": self.avoid_highways
        }

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of warnings/errors."""
        warnings = []

        # Check for required LLM configuration
        if not self.has_llm_config():
            warnings.append(
                "No LLM API key configured. Location parsing accuracy may be reduced. "
                "Set GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in your environment."
            )

        # Check browser configuration
        if self.default_browser != "chromium":
            warnings.append(
                f"Browser '{self.default_browser}' is not supported. "
                "Only Chrome/Chromium is supported per requirements."
            )

        # Check performance settings
        if self.timeout_ms > 10000:
            warnings.append(
                f"Timeout ({self.timeout_ms}ms) exceeds 10-second performance target."
            )

        # Check map provider configuration
        if self.map_provider not in ["gaode", "baidu", "tencent"]:
            warnings.append(
                f"Map provider '{self.map_provider}' may not be fully supported."
            )

        # Check cache directory permissions
        try:
            cache_path = Path(self.cache_dir)
            if cache_path.exists():
                # Test write permissions
                test_file = cache_path / ".test_write"
                test_file.touch()
                test_file.unlink()
        except (OSError, PermissionError):
            warnings.append(
                f"Cache directory '{self.cache_dir}' is not writable. Caching will be disabled."
            )

        return warnings

    def to_dict(self) -> dict:
        """Convert configuration to dictionary (excluding sensitive values)."""
        config_dict = self.dict()

        # Mask sensitive values
        sensitive_keys = [
            'google_api_key', 'openai_api_key', 'anthropic_api_key'
        ]

        for key in sensitive_keys:
            if key in config_dict and config_dict[key]:
                # Show first 8 characters followed by asterisks
                value = config_dict[key]
                if len(value) > 8:
                    config_dict[key] = value[:8] + '*' * (len(value) - 8)
                else:
                    config_dict[key] = '*' * len(value)

        return config_dict


# Global configuration instance
_config_instance: Optional[NavigationConfig] = None


def get_config() -> NavigationConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = NavigationConfig()
    return _config_instance


def load_config(config_file: Optional[Path] = None) -> NavigationConfig:
    """Load configuration from file or environment."""
    global _config_instance

    kwargs = {}
    if config_file and config_file.exists():
        kwargs = {"env_file": str(config_file)}

    _config_instance = NavigationConfig(**kwargs)
    return _config_instance


def reload_config() -> NavigationConfig:
    """Reload configuration from environment variables."""
    global _config_instance
    _config_instance = NavigationConfig()
    return _config_instance