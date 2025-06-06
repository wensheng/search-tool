"""
search_tool: Unified web search interface package.
"""

from .search import SearchTool
from .config import SearchConfig, SearchEngine, SafeSearch, TimeRange
from .playwright_manager import PlaywrightManager
from .models import (
    BaseResult,
    WebResult,
    ImageResult,
    VideoResult,
    NewsResult,
    SearchResults
)
from .exceptions import (
    SearchToolError,
    SearchEngineError,
    ParsingError,
    PlaywrightError,
    ConfigurationError
)

__all__ = [
    "SearchTool",
    "SearchConfig",
    "SearchEngine",
    "SafeSearch",
    "TimeRange",
    "BaseResult",
    "WebResult",
    "ImageResult",
    "VideoResult",
    "NewsResult",
    "SearchResults",
    "SearchToolError",
    "SearchEngineError",
    "ParsingError",
    "PlaywrightError",
    "PlaywrightManager",
    "ConfigurationError",
]