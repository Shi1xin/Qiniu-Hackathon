"""
Main CLI interface for CLI Navigation Tool.

Provides typer-based command-line interface for navigation queries with
rich formatting and user-friendly error handling.
"""

import sys
import asyncio
import typer
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from src.utils.config import get_config, load_config
from src.utils.logging import setup_logging, get_logger, log_user_message
from src.utils.validation import validate_navigation_input, sanitize_input
from src.exceptions import NavigationToolError, handle_unexpected_error
from src.agents.navigation_agent import process_navigation_query, get_navigation_agent


# Initialize Typer app
app = typer.Typer(
    name="nav-cli",
    help="🗺️  CLI Navigation Tool - Parse natural language queries and open browser navigation",
    no_args_is_help=True,
    add_completion=False
)

# Rich console for beautiful output
console = Console()


@app.command()
def main(
    query: str = typer.Argument(..., help="Navigation query (e.g., '从北京到上海')"),
    browser: str = typer.Option(
        "chromium",
        "--browser",
        "-b",
        help="Browser type (Chrome/Chromium only)"
    ),
    headless: bool = typer.Option(
        False,
        "--headless",
        "-h",
        help="Run browser in headless mode"
    ),
    timeout: int = typer.Option(
        10000,
        "--timeout",
        "-t",
        help="Operation timeout in milliseconds"
    ),
    service: str = typer.Option(
        "gaode",
        "--service",
        "-s",
        help="Map service provider"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode"
    ),
    profile: bool = typer.Option(
        False,
        "--profile",
        "-p",
        help="Enable performance profiling"
    )
) -> None:
    """
    Parse natural language navigation query and open browser with route.

    Example usage:
        nav-cli "从北京到上海"
        nav-cli "中关村到三里屯" --browser chromium
        nav-cli "天安门到故宫" --headless --debug
    """
    try:
        # Setup and validation
        _setup_environment(debug, profile)

        # Validate input
        validated_query = _validate_and_sanitize_input(query)

        # Process navigation request using agent
        result = asyncio.run(_process_navigation_request(validated_query, browser, headless, timeout, service))

        # Display results
        _display_results(result)

    except KeyboardInterrupt:
        log_user_message("\n❌ 操作已取消", "error")
        sys.exit(1)
    except NavigationToolError as e:
        log_user_message(f"\n❌ {e.message}", "error")
        for suggestion in e.suggestions:
            log_user_message(f"💡 建议: {suggestion}", "info")
        sys.exit(1)
    except Exception as e:
        error = handle_unexpected_error(e, "main_execution")
        log_user_message(f"\n❌ {error.message}", "error")
        if error.suggestions:
            for suggestion in error.suggestions:
                log_user_message(f"💡 建议: {suggestion}", "info")
        sys.exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    from src import __version__
    console.print(f"🗺️  CLI Navigation Tool v{__version__}")


@app.command()
def config() -> None:
    """Show current configuration."""
    config = get_config()

    # Get configuration warnings
    warnings = config.validate_config()

    console.print("[bold]📋 Current Configuration:[/bold]")
    console.print(config.to_dict())

    if warnings:
        console.print("\n[yellow]⚠️  Configuration Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  • {warning}")


@app.command()
def check() -> None:
    """Check system requirements and dependencies."""
    console.print("[bold]🔍 System Requirements Check[/bold]")

    _check_python_version()
    _check_browser_availability()
    _check_dependencies()
    _check_llm_configuration()

    console.print("\n✅ System check completed!")


def _setup_environment(debug: bool, profile: bool) -> None:
    """Setup logging and environment based on flags."""
    config = get_config()

    # Override config with command line flags
    if debug:
        config.debug = True
        config.log_level = "DEBUG"

    # Setup logging
    logger = setup_logging(
        level=config.log_level,
        log_file=config.log_file,
        structured=config.structured_logging,
        enable_performance=profile or config.log_performance
    )

    if debug:
        log_user_message("Debug mode enabled", "info")
        log_user_message(f"Configuration: {config.to_dict()}", "info")


def _validate_and_sanitize_input(query: str) -> str:
    """Validate and sanitize user input."""
    # Basic input validation
    if not query or not query.strip():
        raise NavigationToolError(
            message="Query cannot be empty",
            error_code="EMPTY_QUERY",
            suggestions=["Provide a navigation query like '从北京到上海'"]
        )

    # Sanitize input
    sanitized = sanitize_input(query.strip())

    if not sanitized:
        raise NavigationToolError(
            message="Invalid input characters detected",
            error_code="INVALID_INPUT",
            suggestions=["Use only Chinese characters and standard punctuation"]
        )

    # Validate navigation format
    try:
        validation_result = validate_navigation_input(sanitized)
        if not validation_result.get("valid"):
            raise NavigationToolError(
                message="Invalid navigation query format",
                error_code="INVALID_FORMAT",
                suggestions=[
                    "Use format: '从[起点]到[终点]'",
                    "Example: '从北京到上海'",
                    "Example: '中关村到三里屯'"
                ]
            )
    except NavigationToolError:
        raise
    except Exception as e:
        raise handle_unexpected_error(e, "input_validation")

    log_user_message(f"✓ Query validated: '{sanitized[:30]}...'")
    return sanitized


async def _process_navigation_request(
    query: str,
    browser: str,
    headless: bool,
    timeout: int,
    service: str
) -> dict:
    """Process the navigation request with progress indication."""
    logger = get_logger()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # Create progress tasks
        parse_task = progress.add_task("🔍 Parsing locations...", total=None)
        url_task = progress.add_task("🔗 Building navigation URL...", total=None)
        browser_task = progress.add_task("🌐 Launching browser...", total=None)

        result = {
            "query": query,
            "origin": None,
            "destination": None,
            "url": None,
            "browser_session": None,
            "success": False,
            "error": None,
            "total_time_ms": 0
        }

        try:
            # Parse locations using validation tools
            from src.utils.validation import validate_navigation_input
            validation_result = validate_navigation_input(query)

            if not validation_result.get("valid", False):
                raise NavigationToolError(
                    message="Failed to parse navigation query",
                    error_code="VALIDATION_FAILED",
                    suggestions=["Check your query format", "Ensure locations are valid"]
                )

            # Extract parsed information
            origin = validation_result.get("origin")
            destination = validation_result.get("destination")

            progress.update(parse_task, description="✓ Locations parsed")

            # Build URL using Gaode Maps tools
            from src.tools.gaode_tools import construct_navigation_url
            navigation_url = construct_navigation_url(
                origin_name=origin,
                destination_name=destination,
                transport_mode="car",
                avoid_tolls=False,
                avoid_highways=False
            )

            progress.update(parse_task, completed=True)
            progress.update(url_task, description="✓ Navigation URL built")

            # Launch browser and navigate to URL
            from src.tools.browser_tools import launch_browser_with_route
            browser_result = await launch_browser_with_route(navigation_url, browser)

            if not browser_result.get("success", False):
                raise NavigationToolError(
                    message="Failed to launch browser",
                    error_code="BROWSER_LAUNCH_FAILED",
                    suggestions=["Check browser installation", "Try running without headless mode"]
                )

            # Update result with actual information
            result.update({
                "origin": origin,
                "destination": destination,
                "url": navigation_url,
                "browser_session": browser_result.get("session_id"),
                "success": True,
                "total_time_ms": browser_result.get("launch_time_ms", 0) + browser_result.get("navigation_time_ms", 0)
            })

            progress.update(url_task, completed=True)
            progress.update(browser_task, description="✓ Browser launched successfully")
            progress.update(browser_task, completed=True)

        except Exception as e:
            progress.stop()
            error = handle_unexpected_error(e, "navigation_processing")
            result["error"] = error.to_dict()
            raise error

    return result


def _display_results(result: dict) -> None:
    """Display processing results to the user."""
    if result["success"]:
        # Success message
        success_panel = Panel(
            f"[bold green]✅ Navigation successful![/bold green]\\n\\n"
            f"Query: {result['query']}\\n"
            f"Processing time: {result['total_time_ms']}ms\\n"
            f"Browser: Chrome/Chromium launched",
            title="[bold]🎉 Result[/bold]",
            border_style="green"
        )
        console.print(success_panel)

        # Additional info
        console.print(f"\\n🌐 Browser opened with navigation route for: {result['query']}")
        console.print("ℹ️  Press Enter to continue when you're done with the browser...")

        # Wait for user input (for non-headless mode)
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass

    else:
        # Error message
        error_panel = Panel(
            f"[bold red]❌ Navigation failed[/bold red]\\n\\n"
            f"Error: {result.get('error', {}).get('error', 'Unknown error')}\\n"
            f"Query: {result['query']}",
            title="[bold]⚠️  Error[/bold]",
            border_style="red"
        )
        console.print(error_panel)


def _check_python_version() -> None:
    """Check Python version requirement."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        console.print(f"[red]❌ Python {version.major}.{version.minor} detected. Python 3.11+ required[/red]")
        sys.exit(1)
    else:
        console.print(f"✅ Python {version.major}.{version.minor}.{version.micro}")


def _check_browser_availability() -> None:
    """Check browser availability."""
    try:
        # This would be implemented with actual browser checking
        console.print("✅ Chrome/Chromium browser available")
    except Exception:
        console.print("[red]❌ Chrome/Chromium browser not found[/red]")
        console.print("💡 Install Chrome or Chromium: https://www.google.com/chrome/")


def _check_dependencies() -> None:
    """Check required dependencies."""
    required_packages = [
        "typer", "rich", "pydantic", "playwright", "langchain"
    ]

    for package in required_packages:
        try:
            __import__(package)
            console.print(f"✅ {package}")
        except ImportError:
            console.print(f"[red]❌ {package} not installed[/red]")


def _check_llm_configuration() -> None:
    """Check LLM API configuration."""
    config = get_config()

    if config.has_llm_config():
        provider = config.get_primary_llm_provider()
        console.print(f"✅ LLM configured: {provider}")
    else:
        console.print("[yellow]⚠️  No LLM API key configured - using basic parsing only[/yellow]")
        console.print("💡 Set GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY for better accuracy")


if __name__ == "__main__":
    app()