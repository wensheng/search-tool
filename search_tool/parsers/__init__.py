"""
Parsers for the search_tool package.
"""
from .base_parser import BaseHTMLParser
from .google import GoogleHTMLParser
from .duckduckgo import DuckDuckGoHTMLParser
from .brave import BraveHTMLParser

__all__ = [
    "BaseHTMLParser",
    "GoogleHTMLParser",
    "DuckDuckGoHTMLParser",
    "BraveHTMLParser",
]