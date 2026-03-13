"""Browser automation base for academic sources."""

import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class BrowserSource(BaseSource):
    """Base class for sources requiring browser automation."""
    
    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
        **kwargs,
    ):
        """Initialize browser source.
        
        Args:
            timeout: Request timeout in seconds.
            headless: Run browser in headless mode.
            **kwargs: Additional arguments.
        """
        super().__init__(timeout)
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def _init_browser(self) -> None:
        """Initialize browser instance."""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            self.page = await self.context.new_page()
    
    async def _navigate(self, url: str, wait_time: int = 2) -> None:
        """Navigate to URL with human-like behavior.
        
        Args:
            url: Target URL.
            wait_time: Time to wait after navigation.
        """
        if self.page is None:
            await self._init_browser()
        
        await self.page.goto(url, timeout=self.timeout * 1000)
        await asyncio.sleep(wait_time)
    
    async def _wait_for_selector(self, selector: str, timeout: int = 10000) -> None:
        """Wait for selector to appear.
        
        Args:
            selector: CSS selector.
            timeout: Timeout in milliseconds.
        """
        if self.page:
            await self.page.wait_for_selector(selector, timeout=timeout)
    
    async def _fill_input(self, selector: str, text: str, delay: int = 50) -> None:
        """Fill input field with human-like typing.
        
        Args:
            selector: Input selector.
            text: Text to type.
            delay: Delay between keystrokes in ms.
        """
        if self.page:
            await self.page.fill(selector, text)
            await asyncio.sleep(delay / 1000 * len(text))
    
    async def _click(self, selector: str, delay: int = 500) -> None:
        """Click element with human-like behavior.
        
        Args:
            selector: Element selector.
            delay: Delay after click in ms.
        """
        if self.page:
            await self.page.click(selector)
            await asyncio.sleep(delay / 1000)
    
    async def _scroll(self, distance: int = 500) -> None:
        """Scroll page with human-like behavior.
        
        Args:
            distance: Scroll distance in pixels.
        """
        if self.page:
            await self.page.evaluate(f"window.scrollBy(0, {distance})")
            await asyncio.sleep(0.5)
    
    async def close(self) -> None:
        """Close browser instance."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        self.browser = None
        self.context = None
        self.page = None