from urllib.parse import urlencode
from playwright.async_api import Page

from .base_engine import BaseSearchEngine
from ..config import SearchConfig, SearchEngine as SEEnum, SafeSearch, TimeRange
from ..models import WebResult
from ..parsers.duckduckgo import DuckDuckGoHTMLParser
from ..playwright_manager import PlaywrightManager
from ..exceptions import ConfigurationError

class DuckDuckGoEngine(BaseSearchEngine):
    """
    Search engine implementation for DuckDuckGo.
    """

    def __init__(self, config: SearchConfig, playwright_manager: PlaywrightManager):
        super().__init__(config, playwright_manager)
        if self.config.search_engine != SEEnum.duckduckgo:
            raise ConfigurationError(
                f"DuckDuckGoEngine initialized with incorrect search engine: {self.config.search_engine.value}"
            )
        self.parser = DuckDuckGoHTMLParser(config)
        self.pages_needed = 1

    async def _build_search_url(self, query: str, page_no: int = 0) -> str:
        """
        Constructs the DuckDuckGo search URL based on the SearchConfig.
        """
        base_url = "https://duckduckgo.com/?"
        # DDG uses 'q' for query, and other parameters are often set via query params as well.
        query_params = {"q": query}

        # Language and Region: DDG uses 'kl' for region and 'kz' for language (less documented)
        # Example: kl=us-en for US English.
        # For simplicity, we'll try to map. If language is 'en-US', region='us', lang='en'
        # This might need more robust mapping based on DDG's actual supported values.
        if self.config.region and self.config.language:
            lang_code = self.config.language.split('-')[0]
            query_params["kl"] = f"{self.config.region.lower()}-{lang_code.lower()}"
        elif self.config.region: # region only
             query_params["kl"] = self.config.region.lower()
        # No direct language-only param as clear as 'kl' for region-language combo.

        # Safe Search: DDG uses 'kp' parameter: -1 (On), 1 (Off), -2 (Moderate - not always an option)
        if self.config.safe_search == SafeSearch.on:
            query_params["kp"] = "-1"
        elif self.config.safe_search == SafeSearch.off:
            query_params["kp"] = "1"
        elif self.config.safe_search == SafeSearch.moderate:
            query_params["kp"] = "-2" # DDG's moderate is not always explicit

        # Time Range: DDG uses 'df' parameter (e.g., d=day, w=week, m=month, y=year)
        if self.config.time_range:
            if self.config.time_range == TimeRange.past_day:
                query_params["df"] = "d"
            elif self.config.time_range == TimeRange.past_week:
                query_params["df"] = "w"
            elif self.config.time_range == TimeRange.past_month:
                query_params["df"] = "m"
            elif self.config.time_range == TimeRange.past_year:
                query_params["df"] = "y"
            # 'any' is default, no param needed. Custom ranges are not directly supported via simple URL params.

        # Number of results: DDG loads more results via scrolling (infinite scroll).
        # For now, num_results from config will be used by the parser to limit how many it extracts.

        # Headless, User-Agent, Proxy are handled by PlaywrightManager via BaseSearchEngine

        # DDG also has 'ia' for instant answers, 'iaf' for instant answer format, etc.
        # For now, keeping it simple.
        query_params["ia"] = "web" # Focus on web results

        return base_url + urlencode(query_params)

    async def _get_page_results(self, page: Page, page_no: int, query: str) -> list[WebResult]:
        search_url = await self._build_search_url(query, page_no)
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        num_loads = (self.config.num_results - 1) // 10
        for _ in range(num_loads):
            # click "More Results" button
            await page.wait_for_selector("button#more-results", state="visible", timeout=10000)
            await page.click("button#more-results")
            # Scroll down to load more results
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_load_state('networkidle')
            # await page.wait_for_timeout(3000)
        results = await self._parse_results(page)
        return results

    async def _parse_results(self, page: Page) -> list[WebResult]:
        """
        Parses the HTML content from the DuckDuckGo SERP using DuckDuckGoHTMLParser.
        """
        # DDG is generally less prone to aggressive CAPTCHAs or cookie banners than Google.
        # Any specific pre-parse interactions for DDG could be added here if needed.
        return await self.parser.parse(page)