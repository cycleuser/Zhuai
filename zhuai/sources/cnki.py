"""CNKI (China National Knowledge Infrastructure) source with PDF priority."""

import asyncio
import random
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from bs4 import BeautifulSoup
from zhuai.models.paper import Paper
from zhuai.sources.browser_base import BrowserSource


class CNKISource(BrowserSource):
    """CNKI academic source with browser automation.
    
    Features:
    - Prioritizes PDF over CAJ format
    - Supports both Chinese and English interfaces
    - Human-like browsing behavior
    - Cookie-based authentication support
    """
    
    BASE_URL_CN = "https://www.cnki.net"
    BASE_URL_EN = "https://kns.cnki.net/kns8s/search"
    SEARCH_URL_CN = "https://kns.cnki.net/kns8s/search"
    
    MIN_DELAY = 3.0
    MAX_DELAY = 6.0
    
    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
        cookies_path: Optional[str] = None,
        prefer_english: bool = True,
        **kwargs,
    ):
        """Initialize CNKI source.
        
        Args:
            timeout: Request timeout in seconds.
            headless: Run browser in headless mode.
            cookies_path: Path to cookies JSON file for login.
            prefer_english: Use English interface (more likely to have PDF).
            **kwargs: Additional arguments.
        """
        super().__init__(timeout, headless, cookies_path, **kwargs)
        self.prefer_english = prefer_english
    
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
        """Search CNKI for papers.
        
        Args:
            query: Search query (supports Chinese and English).
            max_results: Maximum number of results.
            **kwargs: Additional parameters.
            
        Returns:
            List of papers.
        """
        await self._init_browser()
        
        papers = []
        
        try:
            search_url = self._build_search_url(query)
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
                    print(f"Error parsing CNKI result {idx}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error searching CNKI: {e}")
        
        return papers
    
    def _build_search_url(self, query: str) -> str:
        """Build search URL for CNKI."""
        encoded_query = quote(query)
        
        if self.prefer_english:
            return f"https://kns.cnki.net/kns8s/defaultresult/index?kw={encoded_query}&korder=SU"
        else:
            return f"https://kns.cnki.net/kns8s/defaultresult/index?kw={encoded_query}&korder=SU"
    
    def _find_result_items(self, soup: BeautifulSoup, max_results: int) -> List[Any]:
        """Find result items from page."""
        selectors = [
            "tr[id^='td-']",
            ".result-table-list tbody tr",
            ".s-single-result",
            ".result-item",
        ]
        
        items = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                items = found[:max_results]
                break
        
        return items
    
    async def _parse_result(self, item, index: int) -> Optional[Paper]:
        """Parse a single search result.
        
        Args:
            item: BeautifulSoup element.
            index: Result index.
            
        Returns:
            Paper object or None.
        """
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
        
        date_selectors = [".date", "td.date", ".year"]
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
        """Find PDF download URL, prioritizing PDF over CAJ.
        
        Args:
            item: Result item element.
            source_url: Paper source URL.
            
        Returns:
            PDF URL if available.
        """
        pdf_selectors = [
            "a[href*='.pdf']",
            "a[href*='pdf']",
            "a:contains('PDF')",
            "a[title*='PDF']",
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
        
        caj_selectors = [
            "a[href*='.caj']",
            "a[href*='caj']",
        ]
        
        for selector in caj_selectors:
            elem = item.select_one(selector)
            if elem:
                href = elem.get("href", "")
                if href:
                    return None
        
        if source_url:
            pdf_url = await self._get_pdf_from_detail_page(source_url)
            if pdf_url:
                return pdf_url
        
        return None
    
    async def _get_pdf_from_detail_page(self, url: str) -> Optional[str]:
        """Get PDF URL from paper detail page.
        
        Args:
            url: Paper detail page URL.
            
        Returns:
            PDF URL if available.
        """
        try:
            await self._navigate(url)
            await self._human_delay()
            
            content = await self.page.content()
            soup = BeautifulSoup(content, "lxml")
            
            pdf_selectors = [
                "a[href*='.pdf']",
                "a.pdfdown",
                "a[id*='pdf']",
                "a:contains('PDF下载')",
                "a:contains('Download PDF')",
            ]
            
            for selector in pdf_selectors:
                elem = soup.select_one(selector)
                if elem:
                    href = elem.get("href", "")
                    if href:
                        if href.startswith("http"):
                            return href
                        elif href.startswith("//"):
                            return f"https:{href}"
                        else:
                            return f"https://kns.cnki.net{href}"
            
        except Exception as e:
            print(f"Error getting PDF from detail page: {e}")
        
        return None
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get paper by ID."""
        return None