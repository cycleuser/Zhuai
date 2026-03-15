"""Browser automation base for academic sources with human-like behavior."""

import asyncio
import json
import platform
import random
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from playwright_stealth import Stealth
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


SUPPORTED_BROWSERS = {
    "chrome": {
        "name": "Google Chrome",
        "profile_dirs": {
            "darwin": ["~/Library/Application Support/Google/Chrome"],
            "linux": ["~/.config/google-chrome"],
            "win32": ["~/AppData/Local/Google/Chrome/User Data"],
        },
        "default_profile": "Default",
        "cookie_file": "Cookies",
        "playwright_type": "chromium",
    },
    "edge": {
        "name": "Microsoft Edge",
        "profile_dirs": {
            "darwin": ["~/Library/Application Support/Microsoft Edge"],
            "linux": ["~/.config/microsoft-edge"],
            "win32": ["~/AppData/Local/Microsoft/Edge/User Data"],
        },
        "default_profile": "Default",
        "cookie_file": "Cookies",
        "playwright_type": "chromium",
    },
    "firefox": {
        "name": "Mozilla Firefox",
        "profile_dirs": {
            "darwin": ["~/Library/Application Support/Firefox/Profiles"],
            "linux": ["~/.mozilla/firefox"],
            "win32": ["~/AppData/Roaming/Mozilla/Firefox/Profiles"],
        },
        "default_profile": None,
        "cookie_file": "cookies.sqlite",
        "playwright_type": "firefox",
    },
}


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
        import_browser: Optional[str] = None,
        import_profile: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        **kwargs,
    ):
        """Initialize browser source."""
        super().__init__(timeout)
        self.headless = headless
        self.cookies_path = cookies_path
        self.browser_type = browser_type
        self.import_browser = import_browser
        self.import_profile = import_profile
        self.user_data_dir = user_data_dir
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
        self._last_request_time: float = 0
    
    async def _init_browser(self) -> None:
        """Initialize browser instance."""
        if self.browser is None:
            self._playwright = await async_playwright().start()
            
            if self.import_browser:
                await self._init_with_browser_profile()
            elif self.user_data_dir:
                await self._init_with_user_data()
            else:
                await self._init_standard_browser()
    
    async def _init_standard_browser(self) -> None:
        """Initialize standard browser instance."""
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        
        self.context = await self.browser.new_context(
            user_agent=self._get_random_user_agent(),
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        
        if self.cookies_path:
            await self._load_cookies_from_file()
        
        self.page = await self.context.new_page()
        await Stealth().apply_stealth_async(self.page)
    
    async def _init_with_browser_profile(self) -> None:
        """Initialize browser using imported browser's profile."""
        system = platform.system().lower()
        os_name = "darwin" if system == "darwin" else ("win32" if system == "windows" else "linux")
        
        browser_config = SUPPORTED_BROWSERS.get(self.import_browser)
        if not browser_config:
            print(f"Unknown browser: {self.import_browser}")
            await self._init_standard_browser()
            return
        
        # Find profile directory
        profile_dirs = browser_config["profile_dirs"].get(os_name, [])
        user_data_dir = None
        for dir_path in profile_dirs:
            expanded = Path(dir_path).expanduser()
            if expanded.exists():
                user_data_dir = expanded
                break
        
        if not user_data_dir:
            print(f"Browser profile not found for {self.import_browser}")
            await self._init_standard_browser()
            return
        
        # Find specific profile
        profile_path = None
        if self.import_browser in ["chrome", "edge"]:
            profile_name = self.import_profile or browser_config["default_profile"]
            profile_path = user_data_dir / profile_name
            if not profile_path.exists():
                profile_path = user_data_dir
        elif self.import_browser == "firefox":
            for item in user_data_dir.iterdir():
                if item.is_dir() and item.name.endswith(".default-release"):
                    profile_path = item
                    break
                elif item.is_dir() and "default" in item.name.lower():
                    profile_path = item
        
        if not profile_path or not profile_path.exists():
            print(f"Profile not found for {self.import_browser}")
            await self._init_standard_browser()
            return
        
        # For Firefox, always try to launch with profile first
        if self.import_browser == "firefox":
            await self._init_firefox_with_profile(profile_path, browser_config)
        else:
            # For Chrome/Edge, copy cookies
            await self._init_with_cookies(profile_path, browser_config)
    
    async def _init_firefox_with_profile(self, profile_path: Path, browser_config: Dict) -> None:
        """Initialize Firefox with the user's profile."""
        print(f"\n{'='*60}")
        print(f"Firefox Profile: {profile_path}")
        print(f"{'='*60}")
        
        if self.headless:
            print("Headless mode: importing cookies...")
            await self._init_with_cookies(profile_path, browser_config)
            return
        
        print("\n>>> Attempting to launch Firefox with profile...")
        
        try:
            self.context = await self._playwright.firefox.launch_persistent_context(
                user_data_dir=str(profile_path),
                headless=False,
            )
            
            pages = self.context.pages
            self.page = pages[0] if pages else await self.context.new_page()
            await Stealth().apply_stealth_async(self.page)
            
            print(f">>> Firefox launched with your profile!\n")
            return
            
        except Exception as e:
            print(f">>> Failed to launch Firefox: {e}")
            print(f">>> Falling back to cookie import...\n")
            await self._init_with_cookies(profile_path, browser_config)
    
    async def _init_with_cookies(self, profile_path: Path, browser_config: Dict) -> None:
        """Initialize browser with imported cookies."""
        print(f"Importing cookies from {browser_config['name']}...")
        
        cookies = self._extract_cookies_from_browser(profile_path, browser_config)
        
        playwright_type = browser_config.get("playwright_type", "chromium")
        browser_launcher = getattr(self._playwright, playwright_type)
        
        self.browser = await browser_launcher.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        
        self.context = await self.browser.new_context(
            user_agent=self._get_random_user_agent(),
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        
        if cookies:
            await self.context.add_cookies(cookies)
            print(f"Imported {len(cookies)} cookies from {self.import_browser}")
        
        self.page = await self.context.new_page()
        await Stealth().apply_stealth_async(self.page)
    
    async def _init_with_user_data(self) -> None:
        """Initialize browser with custom user data directory."""
        user_data_path = Path(self.user_data_dir).expanduser()
        
        if not user_data_path.exists():
            print(f"User data directory not found: {user_data_path}")
            await self._init_standard_browser()
            return
        
        print(f"Using user data directory: {user_data_path}")
        
        self.context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_path),
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ],
        )
        
        pages = self.context.pages
        self.page = pages[0] if pages else await self.context.new_page()
        await Stealth().apply_stealth_async(self.page)
    
    async def _setup_context(self) -> None:
        pass
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)
    
    def _extract_cookies_from_browser(
        self,
        profile_path: Path,
        browser_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract cookies from browser profile."""
        cookie_file = profile_path / browser_config["cookie_file"]
        
        if not cookie_file.exists():
            print(f"Cookie file not found: {cookie_file}")
            return []
        
        cookies = []
        
        try:
            if self.import_browser in ["chrome", "edge"]:
                cookies = self._extract_chromium_cookies(cookie_file)
            elif self.import_browser == "firefox":
                cookies = self._extract_firefox_cookies(cookie_file)
        except Exception as e:
            print(f"Error extracting cookies: {e}")
        
        return cookies
    
    def _extract_chromium_cookies(self, cookie_file: Path) -> List[Dict[str, Any]]:
        """Extract cookies from Chromium-based browser."""
        cookies = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_cookie = Path(temp_dir) / "Cookies"
            shutil.copy2(cookie_file, temp_cookie)
            
            try:
                conn = sqlite3.connect(str(temp_cookie))
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT host_key, path, name, value, expires_utc, 
                           is_secure, is_httponly, samesite
                    FROM cookies
                """)
                
                for row in cursor.fetchall():
                    host_key, path, name, value, expires, secure, httponly, samesite = row
                    
                    if not name or not value:
                        continue
                    
                    domain = host_key.lstrip(".")
                    
                    cookie = {
                        "name": str(name),
                        "value": str(value or ""),
                        "domain": domain,
                        "path": str(path or "/"),
                        "secure": bool(secure),
                        "httpOnly": bool(httponly),
                        "sameSite": "Lax",
                    }
                    
                    if expires and expires > 0:
                        expires_seconds = expires // 1000000 - 11644473600
                        if expires_seconds > 0:
                            cookie["expires"] = expires_seconds
                    
                    cookies.append(cookie)
                
                conn.close()
            except Exception as e:
                print(f"Error reading Chromium cookies: {e}")
        
        return cookies
    
    def _extract_firefox_cookies(self, cookie_file: Path) -> List[Dict[str, Any]]:
        """Extract cookies from Firefox browser."""
        cookies = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_cookie = Path(temp_dir) / "cookies.sqlite"
            shutil.copy2(cookie_file, temp_cookie)
            
            try:
                conn = sqlite3.connect(str(temp_cookie))
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT host, path, name, value, expiry, 
                           isSecure, isHttpOnly, sameSite
                    FROM moz_cookies
                """)
                
                for row in cursor.fetchall():
                    host, path, name, value, expiry, secure, httponly, samesite = row
                    
                    if not name or not value:
                        continue
                    
                    domain = host.lstrip(".")
                    
                    cookie = {
                        "name": str(name),
                        "value": str(value or ""),
                        "domain": domain,
                        "path": str(path or "/"),
                        "secure": bool(secure),
                        "httpOnly": bool(httponly),
                        "sameSite": "Lax",
                    }
                    
                    if expiry:
                        if expiry > 10000000000:
                            expiry_seconds = expiry // 1000
                        else:
                            expiry_seconds = int(expiry)
                        if expiry_seconds > 0:
                            cookie["expires"] = expiry_seconds
                    
                    cookies.append(cookie)
                
                conn.close()
            except Exception as e:
                print(f"Error reading Firefox cookies: {e}")
        
        return cookies
    
    async def _load_cookies_from_file(self) -> None:
        """Load cookies from JSON file."""
        if not self.cookies_path:
            return
        
        cookies_file = Path(self.cookies_path)
        if cookies_file.exists():
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
        """Navigate to URL with human-like behavior."""
        if self.page is None:
            await self._init_browser()
        
        await self._rate_limit()
        
        await self.page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
        
        if wait_time is None:
            wait_time = random.uniform(1, 3)
        await asyncio.sleep(wait_time)
    
    async def _scroll_page(self, times: int = 3) -> None:
        """Scroll page with human-like behavior."""
        if not self.page:
            return
        
        for _ in range(times):
            scroll_distance = random.randint(300, 800)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await asyncio.sleep(random.uniform(0.3, 0.8))
    
    async def _wait_for_selector(self, selector: str, timeout: int = 10000) -> None:
        """Wait for selector to appear."""
        if self.page:
            await self.page.wait_for_selector(selector, timeout=timeout)
    
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
    def list_importable_browsers() -> List[Dict[str, str]]:
        """List browsers that can be imported."""
        return [
            {"id": "chrome", "name": "Google Chrome"},
            {"id": "edge", "name": "Microsoft Edge"},
            {"id": "firefox", "name": "Mozilla Firefox"},
        ]
    
    @staticmethod
    def export_cookies_instructions() -> str:
        """Return instructions for exporting cookies from browser."""
        return """
导出 Cookies 说明 / Cookies Export Instructions:

方法一：从 Firefox 导入 (推荐)
Method 1: Import from Firefox (Recommended)

  zhuai search "定和效应" --sources cnki --import-browser firefox --no-headless

重要步骤:
1. 先关闭 Firefox 浏览器
2. 运行上面的命令
3. 程序会启动带有你登录状态的 Firefox
4. 如果出现验证码，在浏览器中手动完成

方法二：使用国际源 (无需验证)
Method 2: Use international sources (No verification)

  zhuai search "summation effect" --sources arxiv crossref pubmed --download

这些源不需要验证，可以直接下载 PDF。

方法三：手动导出 Cookies
Method 3: Manual cookie export

1. 安装 "EditThisCookie" 或 "Cookie Editor" 扩展
2. 登录目标网站
3. 导出 cookies 为 JSON 文件
4. 使用 --cookies-path 参数

常见问题 / FAQ:

Q: 知网显示"安全验证"
A: 这是知网的反爬虫机制。使用 --no-headless 显示浏览器，手动完成验证

Q: Firefox cookies 无效
A: 确保在 Firefox 中已登录知网，并刷新过页面

Q: 找不到浏览器配置
A: 确保浏览器已运行过至少一次
"""