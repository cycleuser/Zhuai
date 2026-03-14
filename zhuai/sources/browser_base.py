"""Browser automation base for academic sources with human-like behavior."""

import asyncio
import random
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class BrowserSource(BaseSource):
    """Base class for sources requiring browser automation."""
    
    MIN_DELAY = 2.0
    MAX_DELAY = 5.0
    SCROLL_DELAY = 0.5
    TYPE_DELAY_MIN = 50
    TYPE_DELAY_MAX = 150
    
    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
        cookies_path: Optional[str] = None,
        browser_type: str = "chromium",
        **kwargs,
    ):
        """Initialize browser source.
        
        Args:
            timeout: Request timeout in seconds.
            headless: Run browser in headless mode.
            cookies_path: Path to cookies JSON file.
            browser_type: Browser type (chromium, firefox, webkit).
            **kwargs: Additional arguments.
        """
        super().__init__(timeout)
        self.headless = headless
        self.cookies_path = cookies_path
        self.browser_type = browser_type
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
        self._last_request_time: float = 0
    
    async def _init_browser(self) -> None:
        """Initialize browser instance with human-like settings."""
        if self.browser is None:
            self._playwright = await async_playwright().start()
            
            browser_launcher = getattr(self._playwright, self.browser_type)
            self.browser = await browser_launcher.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )
            
            self.context = await self.browser.new_context(
                user_agent=self._get_random_user_agent(),
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )
            
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            if self.cookies_path:
                await self._load_cookies()
            
            self.page = await self.context.new_page()
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        ]
        return random.choice(user_agents)
    
    async def _load_cookies(self) -> None:
        """Load cookies from file or browser."""
        if not self.cookies_path:
            return
        
        cookies_file = Path(self.cookies_path)
        if cookies_file.exists():
            import json
            cookies = json.loads(cookies_file.read_text())
            await self.context.add_cookies(cookies)
            print(f"Loaded {len(cookies)} cookies from {self.cookies_path}")
    
    async def _human_delay(self) -> None:
        """Add random human-like delay."""
        delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
        await asyncio.sleep(delay)
    
    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        min_interval = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
        
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        
        self._last_request_time = time.time()
    
    async def _navigate(self, url: str, wait_time: Optional[float] = None) -> None:
        """Navigate to URL with human-like behavior.
        
        Args:
            url: Target URL.
            wait_time: Time to wait after navigation.
        """
        if self.page is None:
            await self._init_browser()
        
        await self._rate_limit()
        
        await self.page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
        
        if wait_time is None:
            wait_time = random.uniform(1, 3)
        await asyncio.sleep(wait_time)
    
    async def _scroll_page(self, times: int = 3) -> None:
        """Scroll page with human-like behavior.
        
        Args:
            times: Number of scroll actions.
        """
        if not self.page:
            return
        
        for _ in range(times):
            scroll_distance = random.randint(300, 800)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await asyncio.sleep(random.uniform(0.3, 0.8))
    
    async def _wait_for_selector(self, selector: str, timeout: int = 10000) -> None:
        """Wait for selector to appear.
        
        Args:
            selector: CSS selector.
            timeout: Timeout in milliseconds.
        """
        if self.page:
            await self.page.wait_for_selector(selector, timeout=timeout)
    
    async def _fill_input(self, selector: str, text: str) -> None:
        """Fill input field with human-like typing.
        
        Args:
            selector: Input selector.
            text: Text to type.
        """
        if not self.page:
            return
        
        await self.page.click(selector)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        for char in text:
            await self.page.keyboard.type(char)
            delay = random.uniform(self.TYPE_DELAY_MIN, self.TYPE_DELAY_MAX) / 1000
            await asyncio.sleep(delay)
    
    async def _click(self, selector: str) -> None:
        """Click element with human-like behavior.
        
        Args:
            selector: Element selector.
        """
        if self.page:
            await self._rate_limit()
            await self.page.click(selector)
            await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async def close(self) -> None:
        """Close browser instance."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        self.browser = None
        self.context = None
        self.page = None
        self._playwright = None
    
    @staticmethod
    def export_cookies_instructions() -> str:
        """Return instructions for exporting cookies from browser."""
        return """
导出 Cookies 说明 / Cookies Export Instructions:

方法一：使用浏览器扩展 (推荐)
Method 1: Use Browser Extension (Recommended)

1. 安装 "EditThisCookie" 或 "Cookie Editor" 扩展
   Install "EditThisCookie" or "Cookie Editor" extension

2. 登录目标网站 (如知网 cnki.net)
   Login to target website (e.g., cnki.net)

3. 点击扩展图标，选择 "Export" / "导出"
   Click extension icon, select "Export"

4. 将导出的 JSON 保存为 cookies.json 文件
   Save exported JSON as cookies.json file

方法二：使用开发者工具
Method 2: Use Developer Tools

1. 按 F12 打开开发者工具
   Press F12 to open Developer Tools

2. 切换到 "Application" / "应用程序" 标签
   Switch to "Application" tab

3. 左侧选择 "Cookies" -> 目标网站
   Select "Cookies" -> target website

4. 手动复制 cookies 到 JSON 文件
   Manually copy cookies to JSON file

JSON 格式示例:
JSON Format Example:
[
  {
    "name": "cookie_name",
    "value": "cookie_value",
    "domain": ".cnki.net",
    "path": "/"
  }
]
"""