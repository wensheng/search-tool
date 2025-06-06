"""
Base class for HTML parsers.
"""
from abc import ABC, abstractmethod
from playwright.async_api import Page # Or pass HTML string if preferred by BaseSearchEngine
from ..models import WebResult
from ..config import SearchConfig # Parsers might need config for context (e.g. num_results)

class BaseHTMLParser(ABC):
    """
    Abstract Base Class for HTML parsers.
    Defines an interface for parsing SERP HTML content into structured SearchResults.
    """

    def __init__(self, config: SearchConfig):
        """
        Initializes the parser with the search configuration.

        Args:
            config: The search configuration, which might be useful for parsing context
                    (e.g., knowing how many results were requested).
        """
        self.config = config

    @abstractmethod
    async def parse(self, page: Page) -> list[WebResult]:
        """
        Parses the HTML content from a Playwright Page object
        and extracts relevant information into SearchResults Pydantic models.

        Args:
            page: The Playwright Page object containing the SERP content.
                  Alternatively, this could be changed to accept raw HTML content (str)
                  if the BaseSearchEngine extracts it first. For now, passing Page
                  allows parsers to interact further if needed (e.g., for lazy-loaded content),
                  though direct interaction should be minimized in parsers.

        Returns:
            A SearchResults object populated with extracted data.
        
        Raises:
            ParsingError: If the HTML content cannot be parsed as expected.
        """
