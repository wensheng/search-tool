import os
import subprocess

from playwright.async_api import async_playwright, BrowserContext, Page, Playwright

from .exceptions import PlaywrightError


user_data_dir = os.path.expanduser(os.path.join("~", ".cache", "playwright_chrome"))
os.makedirs(user_data_dir, exist_ok=True)


class PlaywrightManager:
    """
    Manages Playwright browser instances, contexts, and pages.
    """
    # set up a persistent user data dir so Chrome looks like a real profile
    def __init__(self, headless: bool = True):
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._headless = headless

    async def _ensure_playwright_and_browser(self):
        """Ensures Playwright is started and a browser instance is available."""
        if self._playwright is None:
            try:
                self._playwright = await async_playwright().start()
            except Exception:
                try:
                    print('First time running Playwright, installing dependencies...')
                    subprocess.run(
                        ["playwright", "install", "--with-deps", "chrome"],
                        stdout=subprocess.DEVNULL,
                        check=True)
                    self._playwright = await async_playwright().start()
                # except subprocess.CalledProcessError:
                except Exception as e:
                    raise PlaywrightError(f"Failed to start Playwright: {e}")

        if self._context is None:
            try:
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir,
                    channel="chrome",
                    headless=self._headless,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                    ],
                )
                # inject stealth scripts before any page loads
                await self._context.add_init_script(
                    """
                    // pass the WebDriver test
                    Object.defineProperty(navigator, 'webdriver', {get: () => false});
                    // fake Chrome runtime
                    window.navigator.chrome = {runtime: {}};
                    // mock languages
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    // mock plugins
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    """
                )

            except Exception as e:
                # Attempt to close playwright if browser launch fails
                if self._playwright:
                    await self._playwright.stop()
                    self._playwright = None
                raise PlaywrightError(f"Failed to launch Chromium browser: {e}")

    async def get_page(self) -> Page:
        """
        Provides a new Playwright Page instance.
        Manages browser launch and context creation.
        """
        await self._ensure_playwright_and_browser()

        if self._context is None: # Should not happen if _ensure_playwright_and_browser worked
             raise PlaywrightError("Browser is not available after ensuring playwright and browser.")

        try:
            page = await self._context.new_page()
            return page
        except Exception as e:
            raise PlaywrightError(f"Failed to create new page: {e}")

    async def get_pages(self, pages_needed: int) -> list[Page]:
        """
        Provides new Playwright Page instances.
        Manages browser launch and context creation.
        """
        await self._ensure_playwright_and_browser()

        if self._context is None: # Should not happen if _ensure_playwright_and_browser worked
             raise PlaywrightError("Browser is not available after ensuring playwright and browser.")

        pages = []
        try:
            for _ in range(pages_needed):
                page = await self._context.new_page()
                await page.set_viewport_size({"width": 1920, "height": 1080})
                pages.append(page)
            return pages
        except Exception as e:
            raise PlaywrightError(f"Failed to create new page: {e}")

    async def close_page(self, page: Page):
        """Closes a page and its context."""
        if page and not page.is_closed():
            context = page.context
            try:
                await page.close()
                if context and len(context.pages) == 0: # Close context if no more pages
                    await context.close()
            except Exception as e:
                # Log or handle error during page/context close if necessary
                print(f"Error closing page/context: {e}") # Consider logging instead

    async def close(self):
        """Closes the browser and stops Playwright."""
        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                print(f"Error closing browser: {e}") # Consider logging
            self._context = None
        
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                print(f"Error stopping Playwright: {e}") # Consider logging
            self._playwright = None

    # Optional: Add an __aenter__ and __aexit__ for use as an async context manager
    async def __aenter__(self):
        await self._ensure_playwright_and_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()