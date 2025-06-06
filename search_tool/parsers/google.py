from datetime import datetime, timezone

from playwright.async_api import Page
from pydantic import HttpUrl

from ..models import WebResult
from ..config import SearchConfig
from .base_parser import BaseHTMLParser

class GoogleHTMLParser(BaseHTMLParser):
    """
    Parses HTML content from Google search result pages.
    """

    def __init__(self, config: SearchConfig):
        super().__init__(config)

    async def parse(self, page: Page) -> list[WebResult]:
        """
        Parses the Google SERP HTML from a Playwright Page object.

        Args:
            page: The Playwright Page object containing the SERP content.

        Returns:
            A SearchResults object populated with extracted data.
        """
        try:
            await page.wait_for_selector("#search", timeout=10000)
        except Exception: # Playwright's TimeoutError is playwright._impl._api_types.TimeoutError
            # Fallback or raise ParsingError if the main container isn't found
            # For now, let's try to proceed if #search is not there, maybe layout changed.
            # A more robust solution would check for multiple possible main containers.
            # Or, if #search is critical, raise ParsingError.
            # For this iteration, we'll assume it might fail gracefully if #search is missing
            # and result in empty web_results.
            print("Warning: Main search results container '#search' not found. Parsing might fail or be incomplete.")


        web_results_list: list[WebResult] = []
        
        # Selector for general search result blocks, similar to the original logic
        # Google's structure can be complex; data-rpos was a good heuristic.
        # A more robust approach might involve looking for common parent containers of <h3><a>...</a></h3>
        # and then extracting elements relative to that.
        # For now, sticking to a similar approach as original:
        elements = await page.query_selector_all("#search [data-hveid]") # data-hveid is common on result blocks

        if not elements: # Fallback if data-hveid based selection fails
            elements = await page.query_selector_all("div.g") # .g is a common class for results

        position_counter = 1
        for element in elements:
            title: str | None = None
            url: str | None = None
            snippet: str | None = None
            display_url: str | None = None
            
            title_element = await element.query_selector("h3")
            if title_element:
                title_text_content = await title_element.text_content()
                title = title_text_content.strip() if title_text_content else None

            link_element = await element.query_selector("a[href]") # Ensure it has an href
            if link_element:
                href_attribute = await link_element.get_attribute("href")
                if href_attribute and href_attribute.startswith("http"): # Basic validation
                    url = href_attribute
                    
                    # Attempt to get display URL (often within the <a> tag or nearby)
                    # This is a common pattern, but might need adjustment
                    cite_element = await link_element.query_selector("cite")
                    if cite_element:
                        display_url_text = await cite_element.text_content()
                        display_url = display_url_text.strip() if display_url_text else None
                    elif url: # Fallback to hostname or part of URL if cite not found
                        try:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            display_url = parsed_url.netloc + parsed_url.path.split('/')[0] if parsed_url.path else parsed_url.netloc
                        except ImportError: # Should not happen with pydantic
                            display_url = url.split('/')[2] if len(url.split('/')) > 2 else url


            # Snippet extraction (Google often uses specific class names or structures)
            # The original [data-sncf="1"] might be too specific or change.
            # Let's try a more general approach by looking for text blocks not part of title/URL.
            # This is a placeholder and needs refinement.
            snippet_parts = []
            # Common snippet classes: .VwiC3b, .MUxGbd, .yDYNvb, .lyLwlc
            # This needs to be made more robust.
            # For now, let's try a generic text content approach from a common snippet div
            snippet_divs = await element.query_selector_all("div[data-sncf='1'], div.VwiC3b span, div.MUxGbd span") 
            if snippet_divs:
                for snip_div in snippet_divs:
                    snip_text = await snip_div.text_content()
                    if snip_text:
                        snippet_parts.append(snip_text.strip())
                if snippet_parts:
                    snippet = " ".join(snippet_parts)
            
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
                        # Other fields like raw_html_snippet, sitelinks, etc., need more specific selectors
                    )
                    web_results_list.append(web_result)
                    position_counter += 1
                    if len(web_results_list) >= self.config.num_results:
                        break 
                except Exception as e: # Catch Pydantic validation errors or other issues
                    print(f"Skipping a web result due to parsing/validation error: {e} for title '{title}'")


        # Placeholder for other result types (image, video, news)
        # These would require specific selectors and parsing logic for Google.

        return web_results_list
