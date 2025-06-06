"""
Brave search engine implementation.
"""
from urllib.parse import urlencode
from playwright.async_api import Page

from .base_engine import BaseSearchEngine
from ..config import SearchConfig, SearchEngine as SEEnum
from ..models import WebResult
from ..parsers.brave import BraveHTMLParser
from ..playwright_manager import PlaywrightManager
from ..exceptions import ConfigurationError


class BraveEngine(BaseSearchEngine):
    """
    Search engine implementation for Brave Search.
    """

    results_per_page = 20

    def __init__(self, config: SearchConfig, playwright_manager: PlaywrightManager):
        super().__init__(config, playwright_manager)
        if self.config.search_engine != SEEnum.brave:
            raise ConfigurationError(
                f"BraveEngine initialized with incorrect search engine: {self.config.search_engine.value}"
            )
        self.parser = BraveHTMLParser(config)
        self.pages_needed = (self.config.num_results - 1) // self.results_per_page + 1

    async def _build_search_url(self, query: str, page_no: int = 0) -> str:
        """
        Constructs the Brave Search URL based on the SearchConfig.
        """

        base_url = "https://search.brave.com/search?"
        query_params = {"q": query}

        if page_no > 0:
            query_params["offset"] = str(page_no)

        query_params["source"] = "web"
        return base_url + urlencode(query_params)

    async def _parse_results(self, page: Page) -> list[WebResult]:
        """
        Parses the HTML content from the Brave SERP using BraveHTMLParser.
        """
        return await self.parser.parse(page)
