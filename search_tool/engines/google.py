from urllib.parse import urlencode
from playwright.async_api import Page

from .base_engine import BaseSearchEngine
from ..config import SearchConfig, SearchEngine as SEEnum, SafeSearch, TimeRange
from ..models import WebResult
from ..parsers.google import GoogleHTMLParser
from ..playwright_manager import PlaywrightManager
from ..exceptions import ConfigurationError

class GoogleEngine(BaseSearchEngine):
    """
    Search engine implementation for Google.
    """
    results_per_page = 10

    def __init__(self, config: SearchConfig, playwright_manager: PlaywrightManager):
        super().__init__(config, playwright_manager)
        if self.config.search_engine != SEEnum.google:
            raise ConfigurationError(
                f"GoogleEngine initialized with incorrect search engine: {self.config.search_engine.value}"
            )
        self.parser = GoogleHTMLParser(config)
        self.pages_needed = (self.config.num_results - 1) // self.results_per_page + 1

    async def _build_search_url(self, query: str, page_no: int = 0) -> str:
        """
        Constructs the Google search URL based on the SearchConfig.
        """
        base_url = "https://www.google.com/search?"
        query_params = {"q": query}
        if page_no > 0:
            query_params["start"] = str(page_no * self.results_per_page)

        if self.config.language:
            # Google uses 'hl' for host language (UI) and 'lr' for language restrict
            query_params["hl"] = self.config.language 
            query_params["lr"] = f"lang_{self.config.language.split('-')[0] if '-' in self.config.language else self.config.language}"


        if self.config.region:
            # Google uses 'gl' for geolocation
            query_params["gl"] = self.config.region.upper()

        if self.config.num_results and self.config.num_results > 0:
            # Google uses 'num' for number of results
            query_params["num"] = str(self.config.num_results)
        
        if self.config.safe_search:
            # Google's 'safe' parameter: active=on, images=moderate, off=off
            # Mapping our SafeSearch enum to Google's values
            if self.config.safe_search == SafeSearch.on:
                query_params["safe"] = "active"
            elif self.config.safe_search == SafeSearch.moderate: # Primarily for images, but can be set
                query_params["safe"] = "images" 
            elif self.config.safe_search == SafeSearch.off:
                query_params["safe"] = "off"

        # Time range mapping (Google uses 'tbs=qdr:')
        # qdr:h (past hour), qdr:d (past day), qdr:w (past week), qdr:m (past month), qdr:y (past year)
        tbs_params = []
        if self.config.time_range:
            if self.config.time_range == TimeRange.past_day:
                tbs_params.append("qdr:d")
            elif self.config.time_range == TimeRange.past_week:
                tbs_params.append("qdr:w")
            elif self.config.time_range == TimeRange.past_month:
                tbs_params.append("qdr:m")
            elif self.config.time_range == TimeRange.past_year:
                tbs_params.append("qdr:y")
            # 'any' is default, no param needed. Custom ranges are more complex (tbs=cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY)
            # For now, only supporting predefined qdr values.

        if tbs_params:
            query_params["tbs"] = ",".join(tbs_params)
            
        # The original google_search.py had specific init scripts and persistent context.
        # For now, we rely on PlaywrightManager's default context.
        # These could be added as enhancements to PlaywrightManager or specific overrides here if necessary.
        # Example: await context.add_init_script(...) from original file.
        # This would require `page` or `context` to be accessible here, or `PlaywrightManager` to support it.

        return base_url + urlencode(query_params)

    async def _parse_results(self, page: Page) -> list[WebResult]:
        """
        Parses the HTML content from the Google SERP using GoogleHTMLParser.
        """
        # The original google_search.py had logic for cookie banners and CAPTCHAs.
        # Some basic CAPTCHA check is in BaseSearchEngine.search().
        # Cookie banner logic might be needed here or in a pre-navigation hook if BaseSearchEngine supports it.
        # Example from original:
        # is_visible = await page.locator("button:has-text('I agree')").is_visible()
        # if is_visible:
        #     await page.click("button:has-text('I agree')")
        # This kind of interaction should ideally happen before parsing.
        # For now, assuming the page is ready for parsing after BaseSearchEngine.search() navigates.

        return await self.parser.parse(page)

    # Override search if Google needs very specific pre/post navigation steps not in BaseSearchEngine
    # For now, assuming BaseSearchEngine.search() is sufficient.
    # async def search(self) -> SearchResults:
    #     # Custom pre-navigation steps for Google
    #     page = await self.playwright_manager.get_page(...)
    #     await page.add_init_script(...) # Example
    #     # ... then call super().search() or replicate its logic with modifications
    #     return await super().search() # This would call the BaseSearchEngine's search