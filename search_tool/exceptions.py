"""
Exceptions for the search_tool package.
"""


class SearchToolError(Exception):
    """Base exception class for search_tool errors."""


class SearchEngineError(SearchToolError):
    """Raised when an error occurs within a specific search engine's operations."""


class ParsingError(SearchToolError):
    """Raised when an error occurs during the parsing of search results."""


class PlaywrightError(SearchToolError):
    """Raised when an error occurs related to Playwright operations."""


class ConfigurationError(SearchToolError):
    """Raised when there is an issue with the provided configuration."""
