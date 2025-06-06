"""
Base class for search engines.
"""
import asyncio
from abc import ABC, abstractmethod
from playwright.async_api import Page

from ..config import SearchConfig
from ..models import SearchResults, WebResult
from ..exceptions import SearchEngineError, ParsingError, PlaywrightError
from ..playwright_manager import PlaywrightManager


class BaseSearchEngine(ABC):
    """
    Abstract Base Class for search engine implementations.
    Defines a common interface for performing searches and parsing results.
    """

    def __init__(self, config: SearchConfig, playwright_manager: PlaywrightManager):
        """
        Initializes the search engine with configuration and a Playwright manager.

        Args:
            config: The search configuration.
            playwright_manager: Manager for Playwright browser instances.
        """
        if not isinstance(config, SearchConfig):
            raise TypeError("config must be an instance of SearchConfig")
        if not isinstance(playwright_manager, PlaywrightManager):
            raise TypeError("playwright_manager must be an instance of PlaywrightManager")
        
        self.config = config
        self.playwright_manager = playwright_manager
        self.pages_needed = 1

    @abstractmethod
    async def _build_search_url(self, query: str, page_no: int = 0) -> str:
        """
        Constructs the specific search URL for the engine based on self.config.
        This method must be implemented by subclasses.

        Returns:
            The fully constructed search URL.
        """

    @abstractmethod
    async def _parse_results(self, page: Page) -> list[WebResult]:
        """
        Parses the HTML content of the SERP from the Playwright Page
        and returns populated SearchResults Pydantic models.
        This method will typically delegate to a specific HTML parser.
        This method must be implemented by subclasses.

        Args:
            page: The Playwright Page object containing the SERP content.

        Returns:
            Populated SearchResults Pydantic model.
        """

    async def _get_supported_result_types(self) -> list[str]:
        """
        (Optional) Returns a list of result types (e.g., "web", "image", "video")
        supported by this search engine.
        Defaults to supporting "web" results if not overridden.

        Returns:
            A list of supported result type strings.
        """
        return ["web"] # Default implementation

    async def _get_page_results(self, page: Page, page_no: int, query: str) -> list[WebResult]:
        search_url = await self._build_search_url(query, page_no)
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        # # Basic check for CAPTCHA or block pages - can be made more sophisticated
        # # This is a very simplistic check and might need engine-specific overrides
        # page_title = await page.title()
        # if "CAPTCHA" in page_title or "challenge" in page_title.lower() or "blocked" in page_title.lower():
        #     # Attempt to get content for debugging or more specific error
        #     content_for_error = await page.content()
        #     raise SearchEngineError(
        #         f"Potential CAPTCHA or block page detected for {self.config.search_engine.value}. "
        #         f"Title: {page_title}. URL: {search_url}. Content snippet: {content_for_error[:500]}"
        #        )
        results = await self._parse_results(page)
        return results

    async def search(self, query: str) -> SearchResults:
        """
        Orchestrates the search operation:
        1. Builds the search URL.
        2. Launches a browser page using PlaywrightManager.
        3. Navigates to the URL.
        4. Gets the page content.
        5. Parses the results.
        6. Closes the page.

        Returns:
            Populated SearchResults Pydantic model.
        
        Raises:
            SearchEngineError: If any step in the search process fails.
        """
        try:
            pages: list[Page] = await self.playwright_manager.get_pages(self.pages_needed)
            page_results = []
            for i, page in enumerate(pages):
                page_results.append(self._get_page_results(page, i, query))
            gathered_results = await asyncio.gather(*page_results)
            results = [item for sublist in gathered_results for item in sublist]

            return SearchResults(
                query=query,
                search_engine=self.config.search_engine.value,
                web_results=results,
            )

        except PlaywrightError as e:
            raise SearchEngineError(f"Playwright operation failed during search: {e}")
        except ParsingError as e: # Assuming _parse_results might raise this
            raise SearchEngineError(f"Failed to parse search results: {e}")
        except Exception as e:
            # Catch any other unexpected errors during the search process
            error_url = page.url if page else "Unknown URL"
            raise SearchEngineError(
                f"An unexpected error occurred during search with "
                f"{self.config.search_engine.value} for query '{query}' "
                f"at URL {error_url}: {e}"
            )
        finally:
            if pages:
                for page in pages:
                    await self.playwright_manager.close_page(page)
