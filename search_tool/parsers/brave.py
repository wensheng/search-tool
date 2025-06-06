from playwright.async_api import Page
from datetime import datetime, timezone

from pydantic import HttpUrl

from ..models import WebResult
from ..config import SearchConfig
from .base_parser import BaseHTMLParser


class BraveHTMLParser(BaseHTMLParser):
    """
    Parses HTML content from Brave Search result pages.
    """

    def __init__(self, config: SearchConfig):
        super().__init__(config)

    async def parse(self, page: Page) -> list[WebResult]:
        """
        Parses the Brave Search SERP HTML from a Playwright Page object.

        Args:
            page: The Playwright Page object containing the SERP content.

        Returns:
            A list of WebResult objects populated with extracted data.
        """
        try:
            # Wait for the main results container
            await page.wait_for_selector("#results", timeout=10000)
        except Exception: # Playwright's TimeoutError
            print("Warning: Main search results container '#results' not found. Parsing might fail or be incomplete.")
            return []

        web_results_list: list[WebResult] = []

        # Brave uses <div class="snippet"> for each result typically
        # Ensure it's a web result snippet
        elements = await page.query_selector_all("#results .snippet[data-type='web']")

        position_counter = 1
        for element in elements:
            title: str | None = None
            url: str | None = None
            snippet: str | None = None
            # display_url: Optional[str] = None

            # Title is often in a <div class="title"> or <a class="title">
            title_element = await element.query_selector(".title")
            if title_element:
                title_text_content = await title_element.text_content()
                title = title_text_content.strip() if title_text_content else None
            
            # Display URL in Brave is often in <div class="url"> or <span class="url">
            link_element = await element.query_selector("a")
            if link_element:
                url = await link_element.get_attribute("href")

            snippet_container = await element.query_selector(".snippet-content, p.snippet-description, div.desc")
            if snippet_container:
                snippet_text_content = await snippet_container.text_content()
                snippet = snippet_text_content.strip() if snippet_text_content else None
            
            if title and url:
                try:
                    web_result = WebResult(
                        search_engine=self.config.search_engine.value,
                        retrieved_at=datetime.now(tz=timezone.utc),
                        title=title,
                        url=HttpUrl(url),
                        snippet=snippet,
                        position=position_counter
                    )
                    web_results_list.append(web_result)
                    position_counter += 1
                    if len(web_results_list) >= self.config.num_results:
                        break
                except Exception as e:
                    print(f"Skipping a Brave web result due to parsing/validation error: {e} for title '{title}'")

        return web_results_list
