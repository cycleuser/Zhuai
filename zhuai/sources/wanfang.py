"""Wanfang Data source with PDF priority and human-like behavior."""

import asyncio
import random
import re
from datetime import datetime
from typing import List, Optional, Any
from urllib.parse import quote
from bs4 import BeautifulSoup
from zhuai.models.paper import Paper
from zhuai.sources.browser_base import BrowserSource


class WanfangSource(BrowserSource):
    """Wanfang Data source with browser automation.
    
    Features:
    - Prioritizes PDF format
    - Human-like browsing behavior
    - Cookie-based authentication support
    """
    
    BASE_URL = "https://www.wanfangdata.com.cn"
    SEARCH_URL = "https://www.wanfangdata.com.cn/search"
    
    MIN_DELAY = 3.0
    MAX_DELAY = 6.0
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "Wanfang"
    
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
        """Search Wanfang for papers.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Additional parameters.
            
        Returns:
            List of papers.
        """
        await self._init_browser()
        
        papers = []
        
        try:
            encoded_query = quote(query)
            search_url = f"{self.SEARCH_URL}?q={encoded_query}&type=article"
            
            await self._navigate(search_url)
            await self._scroll_page(times=2)
            await self._human_delay()
            
            content = await self.page.content()
            soup = BeautifulSoup(content, "lxml")
            
            items = self._find_result_items(soup, max_results)
            
            for idx, item in enumerate(items):
                if idx > 0:
                    await self._human_delay()
                
                try:
                    paper = await self._parse_result(item, idx)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    print(f"Error parsing Wanfang result {idx}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error searching Wanfang: {e}")
        
        return papers
    
    def _find_result_items(self, soup: BeautifulSoup, max_results: int) -> List[Any]:
        """Find result items from page."""
        selectors = [
            ".result-item",
            ".article-item",
            "li[class*='result']",
            ".normal-list li",
        ]
        
        items = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                items = found[:max_results]
                break
        
        return items
    
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
            ".title a",
            "h3 a",
            "a.title",
            ".article-title a",
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
            ".authors",
            ".author-name",
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
        
        source_elem = item.select_one(".source, .journal, .periodical")
        if source_elem:
            text = source_elem.get_text(strip=True)
            journal = text
            
            year_match = re.search(r'\d{4}', text)
            if year_match:
                year = int(year_match.group())
        
        date_elem = item.select_one(".date, .year, .publish-date")
        if date_elem:
            text = date_elem.get_text(strip=True)
            year_match = re.search(r'\d{4}', text)
            if year_match:
                year = int(year_match.group())
        
        return journal, year
    
    def _extract_abstract(self, item) -> Optional[str]:
        """Extract abstract from result item."""
        abstract_selectors = [
            ".abstract",
            ".summary",
            ".desc",
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
                    return f"{self.BASE_URL}{href}"
        
        return None
    
    async def _find_pdf_url(self, item, source_url: Optional[str]) -> Optional[str]:
        """Find PDF download URL."""
        pdf_selectors = [
            "a[href*='.pdf']",
            "a[href*='pdf']",
            "a.download",
            "a:contains('PDF')",
        ]
        
        for selector in pdf_selectors:
            elem = item.select_one(selector)
            if elem:
                href = elem.get("href", "")
                if href and "pdf" in href.lower():
                    if href.startswith("http"):
                        return href
                    elif href.startswith("//"):
                        return f"https:{href}"
                    else:
                        return f"{self.BASE_URL}{href}"
        
        return None
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get paper by ID."""
        return None