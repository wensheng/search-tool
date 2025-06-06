"""
Main search tool class.
"""
import asyncio

from .models import SearchResults
from .config import SearchConfig, SearchEngine, SafeSearch, TimeRange
from .playwright_manager import PlaywrightManager
from .exceptions import SearchEngineError, ConfigurationError

from .engines.base_engine import BaseSearchEngine
from .engines.google import GoogleEngine
from .engines.duckduckgo import DuckDuckGoEngine
from .engines.brave import BraveEngine


class SearchTool:
    """
    Orchestrates browser automation to perform web searches and parse results.
    """

    def __init__(self, config: SearchConfig):
        if not isinstance(config, SearchConfig):
            raise ConfigurationError("Invalid SearchConfig provided.")
        self.config = config
        self.playwright_manager = PlaywrightManager(config.headless)

        # Engine registry: Maps SearchEngine enum to engine classes
        self._engines_registry: dict[SearchEngine, type[BaseSearchEngine]] = {
            SearchEngine.google: GoogleEngine,
            SearchEngine.duckduckgo: DuckDuckGoEngine,
            SearchEngine.brave: BraveEngine,  # Using actual BraveEngine
        }

    async def search(self, query: str) -> SearchResults:
        """
        Execute the search based on the provided SearchConfig and return structured SearchResults.
        This method is now asynchronous.
        """
        engine_class = self._engines_registry.get(self.config.search_engine)

        if not engine_class:
            raise SearchEngineError(
                f"Search engine '{self.config.search_engine.value}' is not supported."
            )

        # The PlaywrightManager will be used by the BaseSearchEngine instance
        async with self.playwright_manager:  # Use PlaywrightManager as a context manager
            engine_instance = engine_class(
                config=self.config, playwright_manager=self.playwright_manager
            )
            try:
                return await engine_instance.search(query=query)
            except SearchEngineError as e:
                print(
                    f"Error during search with {self.config.search_engine.value}: {e}"
                )
                raise  # Re-raise the original SearchEngineError
            except Exception as e:
                # Catch any other unexpected errors from the engine's search method
                raise SearchEngineError(
                    f"An unexpected error occurred in {self.config.search_engine.value} engine: {e}"
                ) from e

    async def close(self):
        """Cleanly close the Playwright manager."""
        await self.playwright_manager.close()
