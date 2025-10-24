"""
CLI Navigation Tool

A CLI tool for zero-click navigation queries that parses natural language input
like "从北京到上海" and automatically opens Chrome/Chromium browser to display
Gaode Maps navigation routes.
"""

__version__ = "1.0.0"
__author__ = "CLI Navigation Tool Team"

# Initialize configuration and logging
from src.utils.config import get_config, load_config
from src.utils.logging import setup_logging, get_logger