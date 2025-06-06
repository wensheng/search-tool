from typing import Optional
from datetime import datetime, timezone

from pydantic import HttpUrl
from playwright.async_api import Page

from ..models import WebResult
from ..config import SearchConfig
from .base_parser import BaseHTMLParser

class DuckDuckGoHTMLParser(BaseHTMLParser):
    """
    Parses HTML content from DuckDuckGo search result pages.
    """

    def __init__(self, config: SearchConfig):
        super().__init__(config)

    async def parse(self, page: Page) -> list[WebResult]:
        """
        Parses the DuckDuckGo SERP HTML from a Playwright Page object.

        Args:
            page: The Playwright Page object containing the SERP content.

        Returns:
            A SearchResults object populated with extracted data.
        """
        web_results_list: list[WebResult] = []
        try:
            # Wait for the main results container
            await page.wait_for_selector(".react-results--main", timeout=10000)
        except Exception: # Playwright's TimeoutError
            print("Warning: Main search results container '.react-results--main' not found. Parsing might fail or be incomplete.")
            return web_results_list
        
        # Selector for organic search result articles
        elements = await page.query_selector_all(".react-results--main article[data-testid='result']")
        if not elements: # Fallback if the primary selector fails
             elements = await page.query_selector_all(".react-results--main [data-layout='organic']")


        position_counter = 1
        for element in elements:
            title: str | None = None
            url: str | None = None
            snippet: str | None = None
            display_url: str | None = None

            title_element = await element.query_selector("h2 a[href]") # Title is usually within an H2 and an A tag
            if title_element:
                title_text_content = await title_element.text_content()
                title = title_text_content.strip() if title_text_content else None
                href_attribute = await title_element.get_attribute("href")
                if href_attribute: # DDG links are often relative or need careful handling
                    # For now, assume they are absolute or can be resolved by the browser
                    # A more robust solution might involve page.urljoin(href_attribute) if relative
                    url = href_attribute 
                    
                    # Display URL for DDG is often part of the link text or a sibling/child
                    # Example: <a href="..."><span class="result__url__domain">...</span><span class="result__url__path">...</span></a>
                    # This needs specific selectors for DDG
                    display_url_span = await title_element.query_selector("span[data-testid='result-extras-url-host'], span.result__url__domain")
                    if display_url_span:
                        display_url_text = await display_url_span.text_content()
                        display_url = display_url_text.strip() if display_url_text else None
                    elif url: # Fallback
                        try:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            display_url = parsed_url.netloc
                        except ImportError:
                             display_url = url.split('/')[2] if len(url.split('/')) > 2 else url


            # Snippet extraction for DDG
            # Common selector: div containing the snippet text, often a child of the main result article
            # Example: article > div:nth-child(2) > div (structure varies)
            # Or specific class like .result__snippet
            snippet_element = await element.query_selector("div[data-testid='result-snippet'], .result__snippet")
            if snippet_element:
                snippet_text_content = await snippet_element.text_content()
                snippet = snippet_text_content.strip() if snippet_text_content else None
            
            if title and url:
                try:
                    web_result = WebResult(
                        search_engine=self.config.search_engine.value,
                        retrieved_at=datetime.now(tz=timezone.utc),
                        title=title,
                        url=HttpUrl(url),
                        snippet=snippet,
                        display_url=display_url,
                        position=position_counter
                    )
                    web_results_list.append(web_result)
                    position_counter += 1
                    if len(web_results_list) >= self.config.num_results:
                        break
                except Exception as e:
                    print(f"Skipping a DDG web result due to parsing/validation error: {e} for title '{title}'")

        return web_results_list
