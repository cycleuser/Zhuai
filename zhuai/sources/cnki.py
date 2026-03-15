"""CNKI (China National Knowledge Infrastructure) source with PDF priority."""

import asyncio
import json
import random
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from bs4 import BeautifulSoup
from zhuai.models.paper import Paper
from zhuai.sources.browser_base import BrowserSource
from zhuai.utils.vision_helper import VisionHelper


class CNKISource(BrowserSource):
    """CNKI academic source with browser automation.
    
    Features:
    - Prioritizes PDF over CAJ format
    - Supports both Chinese and English interfaces
    - Human-like browsing behavior
    - Cookie-based authentication support
    - Vision AI powered automatic CAPTCHA solving
    """
    
    BASE_URL = "https://www.cnki.net"
    SEARCH_URL = "https://kns.cnki.net/kns8s/defaultresult/index"
    
    MIN_DELAY = 3.0
    MAX_DELAY = 6.0
    
    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
        cookies_path: Optional[str] = None,
        prefer_english: bool = True,
        vision_model: Optional[str] = "gemma3:4b",
        **kwargs,
    ):
        """Initialize CNKI source."""
        super().__init__(timeout, headless, cookies_path, **kwargs)
        self.prefer_english = prefer_english
        self.vision_model = vision_model
        self._vision_helper: Optional[VisionHelper] = None
    
    @property
    def vision_helper(self) -> VisionHelper:
        """Get vision helper instance."""
        if self._vision_helper is None:
            self._vision_helper = VisionHelper(model=self.vision_model)
        return self._vision_helper
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "CNKI"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return True
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        """Search CNKI for papers with automatic CAPTCHA solving."""
        await self._init_browser()
        
        papers = []
        
        try:
            encoded_query = quote(query)
            search_url = f"{self.SEARCH_URL}?kw={encoded_query}"
            
            print(f"Navigating to CNKI...")
            await self._navigate(search_url, wait_time=8)
            
            await self._handle_verification()
            
            await asyncio.sleep(3)
            await self._scroll_page(times=3)
            await self._human_delay()
            
            items = []
            papers_from_vision = []
            
            for retry in range(3):
                content = await self.page.content()
                soup = BeautifulSoup(content, "lxml")
                
                items = self._find_result_items(soup, max_results)
                
                if items:
                    print(f"Found {len(items)} result items")
                    break
                
                print(f"No results found with CSS, trying Vision AI...")
                try:
                    screenshot = await self.page.screenshot(type="jpeg", quality=80)
                    papers_from_vision = await self._find_results_with_vision(screenshot, max_results, query)
                    if papers_from_vision:
                        papers.extend(papers_from_vision)
                        return papers
                except Exception as e:
                    print(f"Vision parse error: {e}")
                
                print(f"Retrying... ({retry + 1}/3)")
                await asyncio.sleep(3)
                await self._scroll_page(times=2)
            
            for idx, item in enumerate(items):
                if idx > 0:
                    await self._human_delay()
                
                try:
                    paper = await self._parse_result(item, idx)
                    if paper:
                        papers.append(paper)
                        print(f"  {idx+1}. {paper.title[:50]}...")
                except Exception as e:
                    print(f"Error parsing result {idx}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error searching CNKI: {e}")
        
        return papers
    
    async def _handle_verification(self) -> None:
        """Handle CNKI verification/CAPTCHA page using Vision AI."""
        await asyncio.sleep(2)
        
        screenshot = await self.page.screenshot(type="jpeg", quality=80)
        page_info = await self.vision_helper.analyze_page_for_login(screenshot)
        
        print(f"  Page analysis: {page_info.get('page_type', 'unknown')}")
        
        if page_info.get("has_captcha"):
            print(f"  Detected CAPTCHA: {page_info.get('description', '')}")
            await self._solve_captcha_automatically()
        
        if page_info.get("needs_login"):
            print("  Page requires login, checking for imported cookies...")
            
        if not page_info.get("has_captcha") and not page_info.get("needs_login"):
            print("  No verification required")
    
    async def _solve_captcha_automatically(self) -> None:
        """Automatically solve CAPTCHA using Vision AI."""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                await asyncio.sleep(1)
                screenshot = await self.page.screenshot(type="jpeg", quality=80)
                captcha_info = await self.vision_helper.detect_captcha_type(screenshot)
                
                print(f"  CAPTCHA type: {captcha_info.get('type', 'unknown')}")
                
                if not captcha_info.get("has_captcha"):
                    print("  CAPTCHA no longer present")
                    return
                
                solved = await self._try_solve_captcha(captcha_info)
                
                if solved:
                    await asyncio.sleep(2)
                    new_screenshot = await self.page.screenshot(type="jpeg", quality=80)
                    new_info = await self.vision_helper.detect_captcha_type(new_screenshot)
                    
                    if not new_info.get("has_captcha"):
                        print("  CAPTCHA solved!")
                        return
                
                print(f"  Attempt {attempt + 1}/{max_attempts} failed")
                
            except Exception as e:
                print(f"  Error: {e}")
        
        raise RuntimeError("Failed to solve CAPTCHA automatically")
    
    async def _try_solve_captcha(self, captcha_info: Dict[str, Any]) -> bool:
        """Try to solve detected CAPTCHA."""
        captcha_type = captcha_info.get("type", "").lower()
        
        if "滑块" in captcha_type or "slider" in captcha_type:
            return await self._solve_slider_captcha()
        elif "点击" in captcha_type or "click" in captcha_type:
            return await self._solve_click_captcha()
        elif "文字" in captcha_type or "text" in captcha_type:
            return await self._solve_text_captcha()
        else:
            return await self._solve_generic_captcha()
    
    async def _solve_slider_captcha(self) -> bool:
        """Solve slider CAPTCHA."""
        try:
            screenshot = await self.page.screenshot(type="jpeg", quality=80)
            result = await self.vision_helper.solve_slider_captcha(screenshot)
            
            if not result or "drag_distance" not in result:
                return False
            
            drag_distance = result.get("drag_distance", 0)
            print(f"  Slider drag distance: {drag_distance}px")
            
            slider_selectors = [
                ".slide-verify-slider",
                ".slider-btn",
                "[class*='slider']",
                "[class*='drag']",
            ]
            
            slider = None
            for selector in slider_selectors:
                try:
                    slider = await self.page.query_selector(selector)
                    if slider:
                        break
                except Exception:
                    continue
            
            if not slider:
                print("  Could not find slider element")
                return False
            
            box = await slider.bounding_box()
            if not box:
                return False
            
            start_x = box["x"] + box["width"] / 2
            start_y = box["y"] + box["height"] / 2
            
            await self.page.mouse.move(start_x, start_y)
            await self.page.mouse.down()
            
            steps = 10
            for i in range(steps + 1):
                offset_x = drag_distance * i / steps
                await self.page.mouse.move(
                    start_x + offset_x,
                    start_y + random.randint(-2, 2),
                )
                await asyncio.sleep(random.uniform(0.01, 0.03))
            
            await self.page.mouse.up()
            return True
            
        except Exception as e:
            print(f"  Slider solve error: {e}")
            return False
    
    async def _solve_click_captcha(self) -> bool:
        """Solve click CAPTCHA."""
        try:
            screenshot = await self.page.screenshot(type="jpeg", quality=80)
            positions = await self.vision_helper.solve_click_captcha(screenshot)
            
            if not positions:
                return False
            
            print(f"  Click positions: {positions}")
            
            for pos in positions:
                x, y = pos.get("x", 0), pos.get("y", 0)
                await self.page.mouse.click(x, y)
                await asyncio.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"  Click solve error: {e}")
            return False
    
    async def _solve_text_captcha(self) -> bool:
        """Solve text CAPTCHA."""
        try:
            captcha_img = await self.page.query_selector("img[src*='captcha'], img[src*='verify']")
            if not captcha_img:
                return False
            
            screenshot = await captcha_img.screenshot()
            text = await self.vision_helper.solve_text_captcha(screenshot)
            
            if not text:
                return False
            
            print(f"  Captcha text: {text}")
            
            input_selectors = [
                "input[name*='captcha']",
                "input[name*='verify']",
                "input[placeholder*='验证码']",
                "input[placeholder*='captcha']",
            ]
            
            for selector in input_selectors:
                try:
                    input_elem = await self.page.query_selector(selector)
                    if input_elem:
                        await input_elem.fill(text)
                        
                        submit_selectors = [
                            "button[type='submit']",
                            "input[type='submit']",
                            ".submit-btn",
                            ".login-btn",
                        ]
                        for sub_selector in submit_selectors:
                            submit = await self.page.query_selector(sub_selector)
                            if submit:
                                await submit.click()
                                return True
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            print(f"  Text solve error: {e}")
            return False
    
    async def _solve_generic_captcha(self) -> bool:
        """Generic CAPTCHA solver - try clicking obvious elements."""
        try:
            screenshot = await self.page.screenshot(type="jpeg", quality=80)
            
            submit_pos = await self.vision_helper.find_element_position(
                screenshot, "submit button or confirm button"
            )
            
            if submit_pos:
                x, y = submit_pos.get("x", 0), submit_pos.get("y", 0)
                print(f"  Clicking at ({x}, {y})")
                await self.page.mouse.click(x, y)
                return True
            
            return False
            
        except Exception as e:
            print(f"  Generic solve error: {e}")
            return False
    
    def _find_result_items(self, soup: BeautifulSoup, max_results: int) -> List[Any]:
        """Find result items from page."""
        selectors = [
            "tr[id^='td-']",
            ".result-table-list tbody tr",
            "table.result-table-list tr",
            ".s-single-result",
            ".result-item",
            "li.result",
            ".search-result-item",
            "[class*='result']",
            "[class*='item']",
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                return items[:max_results]
        
        return []
    
    async def _find_results_with_vision(
        self, 
        screenshot_bytes: bytes, 
        max_results: int,
        query: str = ""
    ) -> List[Dict[str, Any]]:
        """Use Vision AI to find and parse search results."""
        prompt = f"""这是知网(CNKI)学术论文搜索结果页面。搜索关键词是"{query}"。

请仔细识别页面上的论文搜索结果，提取前 {max_results} 篇论文的信息。

对于每篇论文，提取：
1. title: 论文标题（中文）
2. authors: 作者列表
3. source: 期刊/会议名称
4. year: 发表年份（只保留数字）

请严格按照JSON数组格式回复，不要有其他文字：
[
  {{"title": "论文标题", "authors": ["作者1", "作者2"], "source": "期刊名", "year": 2023}},
  ...
]

如果看不到任何论文结果，返回空数组 []"""
        
        try:
            result = await self.vision_helper.analyze_screenshot(screenshot_bytes, prompt)
            json_start = result.find('[')
            json_end = result.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                items = json.loads(json_str)
                papers = []
                seen_titles = set()
                
                for item in items[:max_results]:
                    title = item.get("title", "")
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        year = item.get("year")
                        if isinstance(year, str):
                            try:
                                year = int(''.join(filter(str.isdigit, year)))
                            except ValueError:
                                year = None
                        
                        paper = Paper(
                            title=title,
                            authors=item.get("authors", []),
                            journal=item.get("source"),
                            publication_date=datetime(year, 1, 1) if year else None,
                            pdf_url=None,
                            source_url=None,
                            citations=0,
                            source=self.name,
                            language="zh",
                        )
                        papers.append(paper)
                        print(f"  Vision parsed: {paper.title[:50]}...")
                return papers
        except Exception as e:
            print(f"Vision parse failed: {e}")
        
        return []
    
    async def _parse_result(self, item, index: int) -> Optional[Paper]:
        """Parse a single search result."""
        title = self._extract_title(item)
        if not title:
            return None
        
        authors = self._extract_authors(item)
        journal, year = self._extract_source_info(item)
        abstract = self._extract_abstract(item)
        source_url = self._extract_source_url(item)
        
        pdf_url = await self._find_pdf_url(item, source_url)
        
        publication_date = datetime(year, 1, 1) if year else None
        
        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=publication_date,
            journal=journal,
            pdf_url=pdf_url,
            source_url=source_url,
            citations=0,
            source=self.name,
            language="zh",
        )
    
    def _extract_title(self, item) -> str:
        """Extract title from result item."""
        title_selectors = [
            "a.fz14",
            ".title a",
            "td.name a",
            "a[title]",
            "a[href*='detail']",
        ]
        
        for selector in title_selectors:
            elem = item.select_one(selector)
            if elem:
                title = elem.get("title") or elem.get_text(strip=True)
                if title:
                    return title
        
        return ""
    
    def _extract_authors(self, item) -> List[str]:
        """Extract authors from result item."""
        author_selectors = [
            ".author",
            "td.author",
            ".authors",
            "td[name='author']",
        ]
        
        for selector in author_selectors:
            elem = item.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                authors = re.split(r'[;；,，、\s]+', text)
                return [a.strip() for a in authors if a.strip()]
        
        return []
    
    def _extract_source_info(self, item) -> tuple:
        """Extract journal and year from result item."""
        journal = None
        year = None
        
        source_selectors = [
            ".source",
            "td.source",
            ".journal",
            "td[name='source']",
        ]
        
        for selector in source_selectors:
            elem = item.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                journal = text
                
                year_match = re.search(r'\d{4}', text)
                if year_match:
                    year = int(year_match.group())
                break
        
        date_selectors = [".date", "td.date", ".year", "td[name='date']"]
        for selector in date_selectors:
            elem = item.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                year_match = re.search(r'\d{4}', text)
                if year_match:
                    year = int(year_match.group())
                    break
        
        return journal, year
    
    def _extract_abstract(self, item) -> Optional[str]:
        """Extract abstract from result item."""
        abstract_selectors = [
            ".abstract",
            ".summary",
            "td.abstract",
        ]
        
        for selector in abstract_selectors:
            elem = item.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return None
    
    def _extract_source_url(self, item) -> Optional[str]:
        """Extract source URL from result item."""
        title_link = item.select_one("a[href]")
        if title_link:
            href = title_link.get("href", "")
            if href:
                if href.startswith("http"):
                    return href
                elif href.startswith("//"):
                    return f"https:{href}"
                else:
                    return f"https://kns.cnki.net{href}"
        
        return None
    
    async def _find_pdf_url(self, item, source_url: Optional[str]) -> Optional[str]:
        """Find PDF download URL, prioritizing PDF over CAJ."""
        pdf_selectors = [
            "a[href*='.pdf']",
            "a[href*='pdf']",
            "a:contains('PDF')",
            "a[title*='PDF']",
            "a.pdfdown",
        ]
        
        for selector in pdf_selectors:
            try:
                elem = item.select_one(selector)
                if elem:
                    href = elem.get("href", "")
                    if href and "pdf" in href.lower():
                        if href.startswith("http"):
                            return href
                        elif href.startswith("//"):
                            return f"https:{href}"
                        else:
                            return f"https://kns.cnki.net{href}"
            except Exception:
                continue
        
        return None
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get paper by ID."""
        return None