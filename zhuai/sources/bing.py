"""Bing Academic source."""

import asyncio
import re
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from zhuai.models.paper import Paper
from zhuai.sources.browser_base import BrowserSource


class BingAcademicSource(BrowserSource):
    """Bing Academic source with browser automation."""
    
    BASE_URL = "https://www.bing.com/academic"
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "Bing Academic"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return False
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        """Search Bing Academic for papers.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Additional parameters.
            
        Returns:
            List of papers.
        """
        await self._init_browser()
        
        search_url = f"{self.BASE_URL}/search?q={query}"
        await self._navigate(search_url)
        
        await asyncio.sleep(3)
        
        papers = []
        
        try:
            content = await self.page.content()
            soup = BeautifulSoup(content, "lxml")
            
            items = soup.find_all("div", class_="aca_card")[:max_results]
            
            for item in items:
                try:
                    paper = self._parse_result(item)
                    if paper:
                        papers.append(paper)
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error searching Bing Academic: {e}")
        
        return papers
    
    def _parse_result(self, item) -> Optional[Paper]:
        """Parse a single search result."""
        title_elem = item.find("a", class_="title")
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        
        authors = []
        author_elem = item.find("div", class_="author")
        if author_elem:
            authors = [a.strip() for a in author_elem.get_text(strip=True).split(",") if a.strip()]
        
        journal = None
        venue_elem = item.find("span", class_="venue")
        if venue_elem:
            journal = venue_elem.get_text(strip=True)
        
        year = None
        year_elem = item.find("span", class_="year")
        if year_elem:
            year_text = year_elem.get_text(strip=True)
            year_match = re.search(r"\d{4}", year_text)
            if year_match:
                year = int(year_match.group())
        
        abstract = None
        abstract_elem = item.find("div", class_="abstract")
        if abstract_elem:
            abstract = abstract_elem.get_text(strip=True)
        
        source_url = None
        if title_elem and title_elem.get("href"):
            source_url = title_elem["href"]
        
        publication_date = datetime(year, 1, 1) if year else None
        
        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=publication_date,
            journal=journal,
            pdf_url=None,
            source_url=source_url,
            citations=0,
            source=self.name,
        )
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get paper by ID."""
        return None