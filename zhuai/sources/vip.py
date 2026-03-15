"""VIP (CQVIP) source with Vision AI support."""

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


class VIPSource(BrowserSource):
    """VIP (维普) academic source with Vision AI automation."""
    
    BASE_URL = "https://www.cqvip.com"
    SEARCH_URL = "https://www.cqvip.com/qikan/search"
    
    MIN_DELAY = 3.0
    MAX_DELAY = 6.0
    
    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
        cookies_path: Optional[str] = None,
        vision_model: Optional[str] = "gemma3:4b",
        **kwargs,
    ):
        super().__init__(timeout, headless, cookies_path, **kwargs)
        self.vision_model = vision_model
        self._vision_helper: Optional[VisionHelper] = None
    
    @property
    def vision_helper(self) -> VisionHelper:
        if self._vision_helper is None:
            self._vision_helper = VisionHelper(model=self.vision_model)
        return self._vision_helper
    
    @property
    def name(self) -> str:
        return "VIP"
    
    @property
    def supports_pdf(self) -> bool:
        return True
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        await self._init_browser()
        papers = []
        
        try:
            encoded_query = quote(query)
            search_url = f"{self.SEARCH_URL}?searchword={encoded_query}"
            
            print(f"Navigating to VIP...")
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
            print(f"Error searching VIP: {e}")
        
        return papers
    
    async def _handle_verification(self) -> None:
        await asyncio.sleep(2)
        screenshot = await self.page.screenshot(type="jpeg", quality=80)
        page_info = await self.vision_helper.analyze_page_for_login(screenshot)
        
        if page_info.get("has_captcha"):
            print(f"  Detected CAPTCHA, attempting to solve...")
            await self._solve_captcha_automatically()
    
    async def _solve_captcha_automatically(self) -> None:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                await asyncio.sleep(1)
                screenshot = await self.page.screenshot(type="jpeg", quality=80)
                captcha_info = await self.vision_helper.detect_captcha_type(screenshot)
                
                if not captcha_info.get("has_captcha"):
                    return
                
                solved = await self._try_solve_captcha(captcha_info)
                if solved:
                    await asyncio.sleep(2)
                    return
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        raise RuntimeError("Failed to solve CAPTCHA")
    
    async def _try_solve_captcha(self, captcha_info: Dict[str, Any]) -> bool:
        captcha_type = captcha_info.get("type", "").lower()
        
        if "滑块" in captcha_type or "slider" in captcha_type:
            return await self._solve_slider_captcha()
        elif "点击" in captcha_type or "click" in captcha_type:
            return await self._solve_click_captcha()
        else:
            return await self._solve_generic_captcha()
    
    async def _solve_slider_captcha(self) -> bool:
        try:
            screenshot = await self.page.screenshot(type="jpeg", quality=80)
            result = await self.vision_helper.solve_slider_captcha(screenshot)
            
            if not result or "drag_distance" not in result:
                return False
            
            drag_distance = result.get("drag_distance", 0)
            
            slider_selectors = [".slide-verify-slider", ".slider-btn", "[class*='slider']"]
            slider = None
            for selector in slider_selectors:
                try:
                    slider = await self.page.query_selector(selector)
                    if slider:
                        break
                except Exception:
                    continue
            
            if not slider:
                return False
            
            box = await slider.bounding_box()
            if not box:
                return False
            
            start_x = box["x"] + box["width"] / 2
            start_y = box["y"] + box["height"] / 2
            
            await self.page.mouse.move(start_x, start_y)
            await self.page.mouse.down()
            
            for i in range(11):
                offset_x = drag_distance * i / 10
                await self.page.mouse.move(start_x + offset_x, start_y + random.randint(-2, 2))
                await asyncio.sleep(random.uniform(0.01, 0.03))
            
            await self.page.mouse.up()
            return True
            
        except Exception:
            return False
    
    async def _solve_click_captcha(self) -> bool:
        try:
            screenshot = await self.page.screenshot(type="jpeg", quality=80)
            positions = await self.vision_helper.solve_click_captcha(screenshot)
            
            if not positions:
                return False
            
            for pos in positions:
                x, y = pos.get("x", 0), pos.get("y", 0)
                await self.page.mouse.click(x, y)
                await asyncio.sleep(0.5)
            
            return True
            
        except Exception:
            return False
    
    async def _solve_generic_captcha(self) -> bool:
        try:
            screenshot = await self.page.screenshot(type="jpeg", quality=80)
            submit_pos = await self.vision_helper.find_element_position(screenshot, "submit button")
            
            if submit_pos:
                x, y = submit_pos.get("x", 0), submit_pos.get("y", 0)
                await self.page.mouse.click(x, y)
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _find_results_with_vision(
        self,
        screenshot_bytes: bytes,
        max_results: int,
        query: str = ""
    ) -> List[Dict[str, Any]]:
        prompt = f"""这是维普(VIP)学术论文搜索结果页面。搜索关键词是"{query}"。

请识别页面上的论文搜索结果，提取前 {max_results} 篇论文的信息：
1. title: 论文标题
2. authors: 作者列表
3. source: 期刊/会议名称
4. year: 发表年份

用JSON数组格式回复：
[{{"title": "论文标题", "authors": ["作者1"], "source": "期刊名", "year": 2023}}]

如果看不到论文结果，返回 []"""
        
        try:
            result = await self.vision_helper.analyze_screenshot(screenshot_bytes, prompt)
            json_start = result.find('[')
            json_end = result.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                items = json.loads(result[json_start:json_end])
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
    
    def _find_result_items(self, soup: BeautifulSoup, max_results: int) -> List[Any]:
        selectors = [
            ".list-item",
            ".result-item",
            "li[class*='item']",
            ".article-list li",
            "[class*='result']",
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                return items[:max_results]
        
        return []
    
    async def _parse_result(self, item, index: int) -> Optional[Paper]:
        title = self._extract_title(item)
        if not title:
            return None
        
        authors = self._extract_authors(item)
        journal, year = self._extract_source_info(item)
        source_url = self._extract_source_url(item)
        
        publication_date = datetime(year, 1, 1) if year else None
        
        return Paper(
            title=title,
            authors=authors,
            abstract=None,
            publication_date=publication_date,
            journal=journal,
            pdf_url=None,
            source_url=source_url,
            citations=0,
            source=self.name,
            language="zh",
        )
    
    def _extract_title(self, item) -> str:
        selectors = [".title a", "h3 a", "a.title", ".article-title", "a[href]"]
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                title = elem.get("title") or elem.get_text(strip=True)
                if title:
                    return title
        return ""
    
    def _extract_authors(self, item) -> List[str]:
        selectors = [".author", ".authors", ".author-name"]
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                authors = re.split(r'[;；,，、\s]+', text)
                return [a.strip() for a in authors if a.strip()]
        return []
    
    def _extract_source_info(self, item) -> tuple:
        journal = None
        year = None
        
        source_elem = item.select_one(".source, .journal, .periodical")
        if source_elem:
            text = source_elem.get_text(strip=True)
            journal = text
            year_match = re.search(r'\d{4}', text)
            if year_match:
                year = int(year_match.group())
        
        return journal, year
    
    def _extract_source_url(self, item) -> Optional[str]:
        title_link = item.select_one("a[href]")
        if title_link:
            href = title_link.get("href", "")
            if href:
                if href.startswith("http"):
                    return href
                elif href.startswith("//"):
                    return f"https:{href}"
                else:
                    return f"{self.BASE_URL}{href}"
        return None
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        return None