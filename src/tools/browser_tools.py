"""
Browser automation tools using Playwright.

Provides Chrome/Chromium browser launching, navigation, and connection
pooling capabilities for the CLI Navigation Tool.
"""

import asyncio
import time
from typing import Dict, Optional, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from src.models.browser import BrowserSession, BrowserType, BrowserStatus, BrowserPool
from src.models.results import ProcessingResult, create_browser_error_result, create_success_result
from src.exceptions import (
    BrowserNotAvailableError, BrowserLaunchError, NavigationError,
    TimeoutError, handle_unexpected_error
)
from src.utils.config import get_config
from src.utils.logging import get_logger
from src.utils.performance import performance_timer


class PlaywrightBrowserManager:
    """Manages browser sessions using Playwright."""

    def __init__(self):
        """Initialize the browser manager."""
        self.config = get_config()
        self.logger = get_logger()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.active_sessions: Dict[str, BrowserSession] = {}
        self.browser_pool = BrowserPool()

    async def launch_browser(
        self,
        browser_type: str = "chromium",
        headless: bool = False,
        window_size: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Launch a new browser session."""
        try:
            with performance_timer("browser_launch"):
                # Ensure browser type is supported
                if browser_type != "chromium":
                    raise BrowserNotAvailableError(
                        f"Browser '{browser_type}' not supported. Only Chrome/Chromium is supported."
                    )

                # Launch browser if not already launched
                if self.browser is None:
                    self.browser = await self._initialize_playwright_browser(browser_type)

                # Create browser context
                context_options = self._get_context_options(headless, window_size)
                self.context = await self.browser.new_context(**context_options)

                # Create browser session
                session = BrowserSession(
                    browser_type=BrowserType.CHROMIUM,
                    headless=headless,
                    window_size=window_size or self.config.get_window_dimensions()
                )

                session.mark_ready()

                # Store session
                self.active_sessions[session.session_id] = session

                self.logger.info(f"Browser session created: {session.session_id}")

                return {
                    "success": True,
                    "session_id": session.session_id,
                    "session": session.to_dict(),
                    "launch_time_ms": session.launch_time_ms
                }

        except Exception as e:
            error = handle_unexpected_error(e, "launch_browser")
            self.logger.log_error(error, "browser_launch")

            return {
                "success": False,
                "error": error.message,
                "error_details": error.details
            }

    async def navigate_to_url(self, session_id: str, url: str) -> Dict[str, Any]:
        """Navigate browser session to specified URL."""
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "error": f"Session {session_id} not found",
                    "error_type": "invalid_session"
                }

            session = self.active_sessions[session_id]
            session.mark_navigating(url)

            with performance_timer("browser_navigation"):
                # Create new page if needed
                page = await self.context.new_page()

                # Set additional page settings
                await self._configure_page(page)

                # Navigate to URL
                await page.goto(url, timeout=30000)  # 30 second timeout

                # Wait for page to load
                await page.wait_for_load_state("domcontentloaded", timeout=10000)

                session.mark_navigation_complete(url, await page.title(), session.navigation_time_ms)

                await page.close()

            return {
                "success": True,
                "session_id": session_id,
                "url": url,
                "page_title": session.page_title,
                "navigation_time_ms": session.navigation_time_ms
            }

        except TimeoutError as e:
            session.add_navigation_error(str(e))
            return {
                "success": False,
                "error": e.message,
                "error_type": "timeout",
                "session_id": session_id
            }

        except Exception as e:
            error = handle_unexpected_error(e, "navigate_to_url")
            session.add_navigation_error(str(error))
            self.logger.log_error(error, "browser_navigation")

            return {
                "success": False,
                "error": error.message,
                "error_type": "navigation_error",
                "session_id": session_id
            }

    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close a browser session."""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.mark_closed()
                del self.active_sessions[session_id]

                self.logger.info(f"Browser session closed: {session_id}")

                return {
                    "success": True,
                    "session_id": session_id,
                    "message": "Session closed successfully"
                }

            return {
                "success": False,
                "error": f"Session {session_id} not found",
                "error_type": "invalid_session"
            }

        except Exception as e:
            error = handle_unexpected_error(e, "close_session")
            self.logger.log_error(error, "close_session")

            return {
                "success": False,
                "error": error.message,
                "error_type": "close_error"
            }

    async def close_all_sessions(self) -> Dict[str, Any]:
        """Close all active browser sessions."""
        session_ids = list(self.active_sessions.keys())
        results = []

        for session_id in session_ids:
            result = await self.close_session(session_id)
            results.append(result)

        return {
            "success": all(r["success"] for r in results),
            "closed_sessions": len(results),
            "total_sessions": len(session_ids),
            "results": results
        }

    async def _initialize_playwright_browser(self, browser_type: str) -> Browser:
        """Initialize Playwright browser with platform-specific settings."""
        try:
            playwright = await async_playwright().start()

            # Browser launch arguments for better performance
            launch_args = self._get_launch_arguments()

            if browser_type == "chromium":
                browser = await playwright.chromium.launch(**launch_args)
            else:
                raise BrowserNotAvailableError(f"Browser '{browser_type}' not supported")

            return browser

        except Exception as e:
            raise BrowserLaunchError(
                browser_type=browser_type,
                reason=f"Failed to launch {browser_type}: {str(e)}"
            )

    def _get_launch_arguments(self) -> Dict[str, Any]:
        """Get browser launch arguments for optimal performance."""
        args = {
            # Performance optimizations
            "--no-sandbox": True,  # Disable sandbox for faster startup
            "--disable-dev-shm-usage": True,  # Use /tmp instead of /dev/shm
            "--disable-gpu": True,  # Disable GPU for faster startup
            "--disable-background-timer-throttling": True,  # Disable background timer throttling
            "--disable-backgrounding-occluded-windows": True,  # Disable backgrounding
            "--disable-renderer-backgrounding": True,  # Disable renderer backgrounding
            "--disable-features": "TranslateUI,BlinkGenPropertyTrees",  # Disable unused features

            # Memory optimizations
            "--memory-pressure-off": True,
            "--max_old_space_size": 512,
            "--optimize-for-size": True,

            # Security/privacy (for better compatibility)
            "--disable-web-security": False,  # Keep security for safety
            "--disable-features": "VizDisplayCompositor",  # Disable some features

            # User agent
            "--user-agent": self._get_user_agent()
        }

        # Platform-specific arguments
        import platform
        if platform.system() == "Linux":
            args.update({
                "--disable-gpu-compositing": True,
                "--disable-accelerated-2d-canvas": True
            })
        elif platform.system() == "Darwin":  # macOS
            args.update({
                "--disable-features": "CanvasOtpRasterization"
            })
        elif platform.system() == "Windows":
            args.update({
                "--disable-gpu-process-crash-dump": True
            })

        return args

    def _get_context_options(self, headless: bool, window_size: Optional[Dict[str, int]]) -> Dict[str, Any]:
        """Get browser context options."""
        options = {
            "viewport": window_size or self.config.get_window_dimensions(),
            "user_agent": self._get_user_agent(),
            "java_script_enabled": True,
            "ignore_https_errors": False,
            "bypass_csp": True
        }

        if headless:
            options["headless"] = True

        return options

    def _get_user_agent(self) -> str:
        """Get appropriate user agent string."""
        if self.config.user_agent:
            return self.config.user_agent

        import platform
        system = platform.system()
        version = platform.version()

        # Construct user agent
        user_agent = f"Mozilla/5.0 ({system} {version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        return user_agent

    async def _configure_page(self, page: Page) -> None:
        """Configure page settings for navigation."""
        # Set timeouts
        page.set_default_timeout(30000)  # 30 seconds
        page.set_default_navigation_timeout(30000)

        # Handle JavaScript errors
        page.on("pageerror", lambda error: self.logger.warning(f"Page error: {error}"))

        # Handle console messages
        page.on("console", lambda msg: self.logger.debug(f"Console: {msg.text}") if msg.type == "error" else None)

        # Wait for page to be ready
        await page.wait_for_load_state("domcontentloaded", timeout=10000)

    def check_browser_availability(self) -> Dict[str, Any]:
        """Check if Chrome/Chromium browser is available."""
        try:
            import platform
            import subprocess
            import shutil

            # Check for browser executable
            browser_names = ["chromium-browser", "chromium", "google-chrome", "chrome"]

            available_browser = None
            for browser_name in browser_names:
                if shutil.which(browser_name):
                    available_browser = browser_name
                    break

            if not available_browser:
                return {
                    "available": False,
                    "error": "Chrome/Chromium browser not found",
                    "suggestions": [
                        "Install Google Chrome from https://www.google.com/chrome/",
                        "Install Chromium from your system package manager",
                        "For macOS: brew install --cask chromium",
                        "For Ubuntu: sudo apt-get install chromium-browser"
                    ]
                }

            # Check browser version
            try:
                if platform.system() == "Linux":
                    result = subprocess.run([available_browser, "--version"], capture_output=True, text=True)
                    version = result.stdout.strip()
                else:
                    version = "Unknown version"

                return {
                    "available": True,
                    "browser": available_browser,
                    "version": version,
                    "path": shutil.which(available_browser)
                }

            except Exception:
                return {
                    "available": True,
                    "browser": available_browser,
                    "version": "Unknown",
                    "path": shutil.which(available_browser)
                }

        except Exception as e:
            return {
                "available": False,
                "error": f"Error checking browser availability: {str(e)}",
                "suggestions": [
                    "Check system permissions",
                    "Try running with administrator privileges"
                ]
            }

    def get_active_session_count(self) -> int:
        """Get count of active browser sessions."""
        return len(self.active_sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id].to_dict()
        return None

    async def cleanup(self) -> None:
        """Clean up all browser resources."""
        try:
            # Close all active sessions
            await self.close_all_sessions()

            # Close browser context
            if self.context:
                await self.context.close()
                self.context = None

            # Close browser
            if self.browser:
                await self.browser.close()
                self.browser = None

            self.logger.info("Browser cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


# Global browser manager instance
_browser_manager: Optional[PlaywrightBrowserManager] = None


def get_browser_manager() -> PlaywrightBrowserManager:
    """Get global browser manager instance."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = PlaywrightBrowserManager()
    return _browser_manager


async def launch_browser_with_route(url: str, browser_type: str = "chromium") -> Dict[str, Any]:
    """Launch browser and navigate to URL."""
    manager = get_browser_manager()

    # Launch browser
    launch_result = await manager.launch_browser(browser_type=browser_type, headless=False)

    if not launch_result["success"]:
        return launch_result

    session_id = launch_result["session_id"]

    # Navigate to URL
    nav_result = await manager.navigate_to_url(session_id, url)

    if not nav_result["success"]:
        return {
            "success": False,
            "error": nav_result["error"],
            "error_type": nav_result.get("error_type", "navigation_failed"),
            "session_id": session_id
        }

    # Combine results
    return {
        "success": True,
        "session_id": session_id,
        "url": url,
        "launch_time_ms": launch_result.get("launch_time_ms", 0),
        "navigation_time_ms": nav_result.get("navigation_time_ms", 0)
    }


async def handle_ambiguous_locations(location_name: str, alternatives: List[str] = None) -> Dict[str, Any]:
    """Handle ambiguous location resolution."""
    # For now, implement basic disambiguation logic
    # In a real implementation, this could involve user interaction

    if not alternatives:
        # Provide common alternatives based on location name
        alternatives = [
            f"{location_name}市",
            f"{location_name}区",
            f"{location_name}站"
        ]

    return {
        "success": True,
        "clarification_needed": True,
        "resolved_location": None,  # Would be resolved by user input
        "alternatives": alternatives,
        "message": f"Location '{location_name}' is ambiguous. Please specify:"
    }


# Utility functions for browser operations
def check_chrome_availability() -> bool:
    """Quick check if Chrome/Chromium is available."""
    try:
        import shutil
        return any(shutil.which(browser) for browser in ["chromium", "chrome", "google-chrome"])
    except ImportError:
        return False


def get_platform_specific_config() -> Dict[str, Any]:
    """Get platform-specific browser configuration."""
    import platform

    system = platform.system()
    architecture = platform.machine()

    config = {
        "system": system,
        "architecture": architecture,
        "default_browser": "chromium",
        "supported_browsers": ["chromium"]
    }

    # Platform-specific settings
    if system == "Linux":
        config.update({
            "display_server": platform.environ.get("DISPLAY", ":0"),
            "font_config": "/etc/fonts"
        })
    elif system == "Darwin":  # macOS
        config.update({
            "mac_version": platform.mac_ver()[0] if platform.mac_ver() else "Unknown"
        })
    elif system == "Windows":
        config.update({
            "windows_version": platform.win32_ver() if platform.win32_ver() else "Unknown"
        })

    return config